#pragma once

#include "common.h"
#include <d3d11.h>
#include <dxgi1_2.h>

/**
 * Screen Capture using Desktop Duplication API
 * 
 * Provides GPU-accelerated screen capture functionality.
 */
class ScreenCapture {
public:
    ScreenCapture();
    ~ScreenCapture();
    
    // Initialize Desktop Duplication API
    bool Initialize();
    
    // Capture current screen frame
    ImageData CaptureScreen();
    
    // Capture specific region
    ImageData CaptureRegion(const Rect& region);
    
    // Encode image to PNG (base64)
    std::string EncodeToPNG(const ImageData& pixels, int width, int height);
    
    // Get screen dimensions
    void GetScreenDimensions(int& width, int& height);
    
private:
    // D3D11 device and context
    ID3D11Device* device_;
    ID3D11DeviceContext* context_;
    
    // Desktop duplication interface
    IDXGIOutputDuplication* duplication_;
    
    // Staging texture for reading pixels
    ID3D11Texture2D* stagingTexture_;
    
    // Screen dimensions
    int screenWidth_;
    int screenHeight_;
    
    // Whether initialized
    bool initialized_;
    
    // Create staging texture
    bool CreateStagingTexture(int width, int height);
    
    // Copy frame to staging texture and read pixels
    ImageData ReadPixels(IDXGIResource* resource);
};

