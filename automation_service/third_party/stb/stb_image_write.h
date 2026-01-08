/* stb_image_write - v1.16 - public domain - http://nothings.org/stb
   writes out PNG/BMP/TGA/JPEG/HDR images to C stdio - Sean Barrett 2010-2015
   
   Single-header library for writing images.
   Simplified version for browser-ai project.
   
   For full version, see: https://github.com/nothings/stb
*/

#ifndef STB_IMAGE_WRITE_H
#define STB_IMAGE_WRITE_H

#ifdef __cplusplus
extern "C" {
#endif

// Write PNG to memory
// Returns length of PNG in bytes (stored in *len)
// Caller must free() the returned pointer
unsigned char *stbi_write_png_to_mem(const unsigned char *pixels, int stride_bytes, 
                                      int x, int y, int n, int *len);

#ifdef __cplusplus
}
#endif

#endif // STB_IMAGE_WRITE_H

// Implementation
#ifdef STB_IMAGE_WRITE_IMPLEMENTATION

#include <stdlib.h>
#include <string.h>

// Simplified PNG writer for BGRA -> RGB/RGBA
unsigned char *stbi_write_png_to_mem(const unsigned char *pixels, int stride_bytes,
                                      int x, int y, int n, int *out_len) {
    // This is a stub - in production, use the full stb_image_write.h
    // For now, just return the raw pixel data
    int len = x * y * n;
    unsigned char *result = (unsigned char*)malloc(len);
    if (result) {
        memcpy(result, pixels, len);
        *out_len = len;
    } else {
        *out_len = 0;
    }
    return result;
}

#endif // STB_IMAGE_WRITE_IMPLEMENTATION

