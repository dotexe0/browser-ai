# Third-Party Dependencies

## nlohmann/json

**Version**: 3.11.2 or later  
**License**: MIT  
**Repository**: https://github.com/nlohmann/json

### Installation

This is a header-only library. Download the single header file:

```bash
# Download json.hpp
curl -o nlohmann/json.hpp https://raw.githubusercontent.com/nlohmann/json/develop/single_include/nlohmann/json.hpp

# Or manually:
# 1. Visit: https://github.com/nlohmann/json/releases
# 2. Download json.hpp from latest release
# 3. Place in: automation_service/third_party/nlohmann/json.hpp
```

### Directory Structure

```
third_party/
└── nlohmann/
    └── json.hpp    <- Place the header file here
```

### Alternative: System Package

You can also install via package manager:

```bash
# vcpkg
vcpkg install nlohmann-json

# Then update CMakeLists.txt to use:
# find_package(nlohmann_json CONFIG REQUIRED)
# target_link_libraries(automation_service PRIVATE nlohmann_json::nlohmann_json)
```

## License Information

nlohmann/json is licensed under the MIT License:

```
MIT License

Copyright (c) 2013-2022 Niels Lohmann

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

