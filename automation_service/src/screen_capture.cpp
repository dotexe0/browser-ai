#include "screen_capture.h"
#include <wincodec.h>
#include <wincodecsdk.h>

#pragma comment(lib, "windowscodecs.lib")

ScreenCapture::ScreenCapture()
    : device_(nullptr)
    , context_(nullptr)
    , duplication_(nullptr)
    , stagingTexture_(nullptr)
    , screenWidth_(0)
    , screenHeight_(0)
    , initialized_(false) {
}

ScreenCapture::~ScreenCapture() {
    if (stagingTexture_) stagingTexture_->Release();
    if (duplication_) duplication_->Release();
    if (context_) context_->Release();
    if (device_) device_->Release();
}

bool ScreenCapture::Initialize() {
    if (initialized_) {
        return true;
    }
    
    // Create D3D11 device
    D3D_FEATURE_LEVEL featureLevel;
    HRESULT hr = D3D11CreateDevice(
        nullptr,
        D3D_DRIVER_TYPE_HARDWARE,
        nullptr,
        0,
        nullptr,
        0,
        D3D11_SDK_VERSION,
        &device_,
        &featureLevel,
        &context_
    );
    
    if (FAILED(hr)) {
        LOG_ERROR(L"Failed to create D3D11 device");
        return false;
    }
    
    // Get DXGI device
    IDXGIDevice* dxgiDevice = nullptr;
    hr = device_->QueryInterface(__uuidof(IDXGIDevice), reinterpret_cast<void**>(&dxgiDevice));
    if (FAILED(hr)) {
        LOG_ERROR(L"Failed to get DXGI device");
        return false;
    }
    
    // Get DXGI adapter
    IDXGIAdapter* dxgiAdapter = nullptr;
    hr = dxgiDevice->GetAdapter(&dxgiAdapter);
    dxgiDevice->Release();
    
    if (FAILED(hr)) {
        LOG_ERROR(L"Failed to get DXGI adapter");
        return false;
    }
    
    // Get output (monitor)
    IDXGIOutput* dxgiOutput = nullptr;
    hr = dxgiAdapter->EnumOutputs(0, &dxgiOutput);
    dxgiAdapter->Release();
    
    if (FAILED(hr)) {
        LOG_ERROR(L"Failed to enumerate outputs");
        return false;
    }
    
    // Get output1 interface for desktop duplication
    IDXGIOutput1* dxgiOutput1 = nullptr;
    hr = dxgiOutput->QueryInterface(__uuidof(IDXGIOutput1), reinterpret_cast<void**>(&dxgiOutput1));
    dxgiOutput->Release();
    
    if (FAILED(hr)) {
        LOG_ERROR(L"Failed to get IDXGIOutput1");
        return false;
    }
    
    // Get screen dimensions
    DXGI_OUTPUT_DESC outputDesc;
    dxgiOutput1->GetDesc(&outputDesc);
    screenWidth_ = outputDesc.DesktopCoordinates.right - outputDesc.DesktopCoordinates.left;
    screenHeight_ = outputDesc.DesktopCoordinates.bottom - outputDesc.DesktopCoordinates.top;
    
    // Create desktop duplication
    hr = dxgiOutput1->DuplicateOutput(device_, &duplication_);
    dxgiOutput1->Release();
    
    if (FAILED(hr)) {
        LOG_ERROR(L"Failed to create desktop duplication");
        return false;
    }
    
    // Create staging texture
    if (!CreateStagingTexture(screenWidth_, screenHeight_)) {
        return false;
    }
    
    initialized_ = true;
    LOG_INFO(L"Screen capture initialized successfully");
    return true;
}

bool ScreenCapture::CreateStagingTexture(int width, int height) {
    D3D11_TEXTURE2D_DESC desc = {};
    desc.Width = width;
    desc.Height = height;
    desc.MipLevels = 1;
    desc.ArraySize = 1;
    desc.Format = DXGI_FORMAT_B8G8R8A8_UNORM;
    desc.SampleDesc.Count = 1;
    desc.Usage = D3D11_USAGE_STAGING;
    desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
    
    HRESULT hr = device_->CreateTexture2D(&desc, nullptr, &stagingTexture_);
    
    if (FAILED(hr)) {
        LOG_ERROR(L"Failed to create staging texture");
        return false;
    }
    
    return true;
}

ImageData ScreenCapture::CaptureScreen() {
    if (!initialized_) {
        throw std::runtime_error("Screen capture not initialized");
    }
    
    IDXGIResource* desktopResource = nullptr;
    DXGI_OUTDUPL_FRAME_INFO frameInfo;
    
    // Acquire next frame
    HRESULT hr = duplication_->AcquireNextFrame(500, &frameInfo, &desktopResource);
    
    if (hr == DXGI_ERROR_WAIT_TIMEOUT) {
        // No new frame available, try to get current desktop
        LOG_DEBUG(L"Frame timeout, retrying");
        return ImageData();
    }
    
    if (FAILED(hr)) {
        LOG_ERROR(L"Failed to acquire frame");
        return ImageData();
    }
    
    // Read pixels from frame
    ImageData pixels = ReadPixels(desktopResource);
    
    // Release frame
    desktopResource->Release();
    duplication_->ReleaseFrame();
    
    return pixels;
}

ImageData ScreenCapture::ReadPixels(IDXGIResource* resource) {
    // Get texture from resource
    ID3D11Texture2D* texture = nullptr;
    HRESULT hr = resource->QueryInterface(__uuidof(ID3D11Texture2D), reinterpret_cast<void**>(&texture));
    
    if (FAILED(hr)) {
        LOG_ERROR(L"Failed to get texture from resource");
        return ImageData();
    }
    
    // Copy to staging texture
    context_->CopyResource(stagingTexture_, texture);
    texture->Release();
    
    // Map staging texture to read pixels
    D3D11_MAPPED_SUBRESOURCE mapped;
    hr = context_->Map(stagingTexture_, 0, D3D11_MAP_READ, 0, &mapped);
    
    if (FAILED(hr)) {
        LOG_ERROR(L"Failed to map staging texture");
        return ImageData();
    }
    
    // Copy pixels
    ImageData pixels(screenWidth_ * screenHeight_ * 4); // BGRA format
    
    byte* src = static_cast<byte*>(mapped.pData);
    byte* dst = pixels.data();
    
    for (int y = 0; y < screenHeight_; y++) {
        memcpy(dst, src, screenWidth_ * 4);
        src += mapped.RowPitch;
        dst += screenWidth_ * 4;
    }
    
    context_->Unmap(stagingTexture_, 0);
    
    return pixels;
}

ImageData ScreenCapture::CaptureRegion(const Rect& region) {
    // For now, capture full screen and crop
    // TODO: Optimize to capture only region
    ImageData fullScreen = CaptureScreen();
    
    if (fullScreen.empty()) {
        return ImageData();
    }
    
    // Simple cropping
    ImageData cropped;
    // TODO: Implement cropping logic
    
    return cropped;
}

std::string ScreenCapture::EncodeToPNG(const ImageData& pixels, int width, int height) {
    if (pixels.empty()) {
        return "";
    }
    
    // This is a simplified version
    // For base64 encoding, we'd use a library or implement it
    // For now, return placeholder
    return "base64_encoded_png_data";
}

void ScreenCapture::GetScreenDimensions(int& width, int& height) {
    width = screenWidth_;
    height = screenHeight_;
}

