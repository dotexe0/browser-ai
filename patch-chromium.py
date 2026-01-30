#!/usr/bin/env python3
"""
Apply AI Panel integration patches to Chromium source files.

Run after sync-to-chromium.sh. Idempotent - safe to run multiple times.
Patches existing Chromium files to register the AI Panel side panel.
"""

import os
import sys
import re


def find_chromium_src():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chromium_src = os.path.join(script_dir, 'chromium', 'src')
    if not os.path.isdir(chromium_src):
        print(f"Error: Chromium source not found at {chromium_src}")
        sys.exit(1)
    return chromium_src


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


def patch_file(chromium_src, rel_path, marker, description, patch_fn):
    """Apply a patch if not already applied. Returns result status string."""
    full_path = os.path.join(chromium_src, rel_path)
    if not os.path.isfile(full_path):
        print(f"  [WARN] File not found: {rel_path}")
        return 'missing'

    content = read_file(full_path)
    if marker in content:
        print(f"  [SKIP] {description} (already applied)")
        return 'skip'

    new_content = patch_fn(content)
    if new_content is None:
        print(f"  [FAIL] {description} (anchor pattern not found)")
        return 'fail'

    write_file(full_path, new_content)
    print(f"  [OK]   {description}")
    return 'ok'


# ---------------------------------------------------------------------------
# Patch functions - each transforms file content and returns new content
# Returns None if the anchor pattern wasn't found
# ---------------------------------------------------------------------------

def patch_side_panel_entry_id(content):
    """Add kAIPanel to SIDE_PANEL_ENTRY_IDS macro."""
    lines = content.split('\n')
    insert_idx = None

    # Find the last V(kXxx, kActionXxx, "Xxx") \ line in the macro
    for i, line in enumerate(lines):
        if re.match(r'\s*V\(k\w+,\s*kAction\w+,\s*"[^"]+"\)\s*\\', line):
            insert_idx = i

    if insert_idx is None:
        return None

    indent = re.match(r'(\s*)', lines[insert_idx]).group(1)
    new_line = f'{indent}V(kAIPanel, kActionSidePanelShowAIPanel, "AIPanel") \\'
    lines.insert(insert_idx + 1, new_line)
    return '\n'.join(lines)


def patch_chrome_action_id(content):
    """Add kActionSidePanelShowAIPanel to SIDE_PANEL_ACTION_IDS macro."""
    lines = content.split('\n')
    insert_idx = None

    # The side panel actions use the E() macro format inside a #define, e.g.:
    #   E(kActionSidePanelShowMerchantTrust)
    # Find the last E(kActionSidePanelShow...) entry
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'E\(kActionSidePanelShow\w+', stripped):
            insert_idx = i

    if insert_idx is None:
        return None

    indent = re.match(r'(\s*)', lines[insert_idx]).group(1)
    # The last entry in the macro has no trailing backslash.
    # We need to add a backslash to the current last line and append our entry.
    if not lines[insert_idx].rstrip().endswith('\\'):
        lines[insert_idx] = lines[insert_idx].rstrip() + ' \\'
    new_line = f'{indent}E(kActionSidePanelShowAIPanel)'
    lines.insert(insert_idx + 1, new_line)
    return '\n'.join(lines)


def patch_chrome_web_ui_configs(content):
    """Add AIPanelUIConfig include and registration."""
    include_line = '#include "chrome/browser/ui/webui/ai_panel/ai_panel_ui.h"'
    reg_line = '  map.AddWebUIConfig(std::make_unique<AIPanelUIConfig>());'

    lines = content.split('\n')

    # Add include after the last #include
    last_include_idx = None
    for i, line in enumerate(lines):
        if line.startswith('#include'):
            last_include_idx = i
    if last_include_idx is None:
        return None
    lines.insert(last_include_idx + 1, include_line)

    # Add registration after the last AddWebUIConfig call
    insert_idx = None
    for i, line in enumerate(lines):
        if 'AddWebUIConfig' in line:
            insert_idx = i
    if insert_idx is None:
        return None
    lines.insert(insert_idx + 1, reg_line)

    return '\n'.join(lines)


def patch_browser_window_features_header(content):
    """Add coordinator include, member, and accessor to browser_window_features.h."""
    include_line = '#include "chrome/browser/ui/views/side_panel/ai_panel/ai_panel_side_panel_coordinator.h"'

    lines = content.split('\n')

    # Add include
    last_include_idx = None
    for i, line in enumerate(lines):
        if line.startswith('#include'):
            last_include_idx = i
    if last_include_idx is None:
        return None
    lines.insert(last_include_idx + 1, include_line)

    # Add member variable near other unique_ptr<*Coordinator> members
    member_idx = None
    for i, line in enumerate(lines):
        if 'std::unique_ptr<' in line and 'coordinator_' in line.lower():
            member_idx = i
    if member_idx is None:
        # Fallback: find any unique_ptr member
        for i, line in enumerate(lines):
            if 'std::unique_ptr<' in line and line.strip().endswith(';'):
                member_idx = i
    if member_idx is None:
        return None

    indent = re.match(r'(\s*)', lines[member_idx]).group(1)
    lines.insert(member_idx + 1,
                 f'{indent}std::unique_ptr<AiPanelSidePanelCoordinator> ai_panel_side_panel_coordinator_;')

    # Add accessor near other *_coordinator() accessors
    accessor_idx = None
    for i, line in enumerate(lines):
        # Look for accessor declarations like: SomeCoordinator* some_coordinator()
        if 'coordinator()' in line and ('*' in line or 'Coordinator' in line):
            accessor_idx = i
            # If it's an inline accessor, skip past closing brace
            if '{' in line:
                j = i
                while j < len(lines) and '}' not in lines[j]:
                    j += 1
                accessor_idx = j

    if accessor_idx is not None:
        indent = re.match(r'(\s*)', lines[accessor_idx]).group(1)
        accessor_lines = [
            f'{indent}AiPanelSidePanelCoordinator* ai_panel_side_panel_coordinator() {{',
            f'{indent}  return ai_panel_side_panel_coordinator_.get();',
            f'{indent}}}',
        ]
        for j, al in enumerate(accessor_lines):
            lines.insert(accessor_idx + 1 + j, al)
    else:
        # Fallback: add before the member we just inserted
        # Re-find it since indices shifted
        for i, line in enumerate(lines):
            if 'ai_panel_side_panel_coordinator_;' in line:
                indent = re.match(r'(\s*)', lines[i]).group(1)
                accessor_lines = [
                    f'{indent}AiPanelSidePanelCoordinator* ai_panel_side_panel_coordinator() {{',
                    f'{indent}  return ai_panel_side_panel_coordinator_.get();',
                    f'{indent}}}',
                ]
                for j, al in enumerate(accessor_lines):
                    lines.insert(i, al)
                break

    return '\n'.join(lines)


def patch_browser_window_features_cc(content):
    """Add coordinator creation in BrowserWindowFeatures Init/constructor."""
    include_line = '#include "chrome/browser/ui/views/side_panel/ai_panel/ai_panel_side_panel_coordinator.h"'

    lines = content.split('\n')

    # Add include if not present
    if include_line not in content:
        last_include_idx = None
        for i, line in enumerate(lines):
            if line.startswith('#include'):
                last_include_idx = i
        if last_include_idx is not None:
            lines.insert(last_include_idx + 1, include_line)

    # Find where other coordinators are created with make_unique and add ours
    content_so_far = '\n'.join(lines)
    lines = content_so_far.split('\n')

    insert_idx = None
    for i, line in enumerate(lines):
        if 'make_unique<' in line and 'Coordinator>' in line:
            # Find end of this statement
            j = i
            while j < len(lines) and ';' not in lines[j]:
                j += 1
            insert_idx = j

    if insert_idx is None:
        # Fallback: find Init() method and insert at end of body
        in_init = False
        brace_depth = 0
        for i, line in enumerate(lines):
            if '::Init(' in line or '::InitFeatures(' in line:
                in_init = True
            if in_init:
                brace_depth += line.count('{') - line.count('}')
                if brace_depth > 0 and ';' in line:
                    insert_idx = i

    if insert_idx is None:
        return None

    creation_lines = [
        '  ai_panel_side_panel_coordinator_ =',
        '      std::make_unique<AiPanelSidePanelCoordinator>(browser);'
    ]
    for j, cl in enumerate(creation_lines):
        lines.insert(insert_idx + 1 + j, cl)

    return '\n'.join(lines)


def patch_side_panel_util(content):
    """Add AI panel registration in PopulateGlobalEntries."""
    include_line = '#include "chrome/browser/ui/views/side_panel/ai_panel/ai_panel_side_panel_coordinator.h"'

    lines = content.split('\n')

    # Add include
    last_include_idx = None
    for i, line in enumerate(lines):
        if line.startswith('#include'):
            last_include_idx = i
    if last_include_idx is None:
        return None
    lines.insert(last_include_idx + 1, include_line)

    # Find PopulateGlobalEntries and add after the last CreateAndRegisterEntry call
    content_so_far = '\n'.join(lines)
    lines = content_so_far.split('\n')

    in_fn = False
    insert_idx = None
    for i, line in enumerate(lines):
        if 'PopulateGlobalEntries' in line:
            in_fn = True
        if in_fn and 'CreateAndRegisterEntry' in line:
            j = i
            while j < len(lines) and ';' not in lines[j]:
                j += 1
            insert_idx = j

    if insert_idx is None:
        return None

    reg_lines = [
        '',
        '  browser->browser_window_features()',
        '      ->ai_panel_side_panel_coordinator()',
        '      ->CreateAndRegisterEntry(window_registry);'
    ]
    for j, rl in enumerate(reg_lines):
        lines.insert(insert_idx + 1 + j, rl)

    return '\n'.join(lines)


def patch_side_panel_build_gn(content):
    """Add ai_panel_side_panel dep to side panel BUILD.gn."""
    dep_line = '    "//chrome/browser/ui/webui/ai_panel:ai_panel_side_panel",'

    lines = content.split('\n')
    insert_idx = None

    # Find deps section - look for existing "//chrome/browser/" deps
    for i, line in enumerate(lines):
        if '"//chrome/browser/' in line and line.strip().endswith(','):
            insert_idx = i

    if insert_idx is None:
        # Fallback: find any deps = [ and add inside
        for i, line in enumerate(lines):
            if 'deps' in line and '=' in line:
                insert_idx = i

    if insert_idx is None:
        return None

    lines.insert(insert_idx + 1, dep_line)
    return '\n'.join(lines)


def patch_browser_resources_grd(content):
    """Add AI panel resource entries to browser_resources.grd."""
    resource_lines = [
        '',
        '      <!-- AI Panel Side Panel -->',
        '      <include name="IDR_AI_PANEL_HTML" file="resources/side_panel/ai_panel/ai_panel.html" type="BINDATA" />',
        '      <include name="IDR_AI_PANEL_JS" file="resources/side_panel/ai_panel/ai_panel.js" type="BINDATA" />',
        '      <include name="IDR_AI_PANEL_CSS" file="resources/side_panel/ai_panel/ai_panel.css" type="BINDATA" />',
        '      <include name="IDR_AI_PANEL_PROVIDER_INTERFACE_JS" file="resources/side_panel/ai_panel/ai_provider_interface.js" type="BINDATA" />',
        '      <include name="IDR_AI_PANEL_OPENAI_PROVIDER_JS" file="resources/side_panel/ai_panel/openai_provider.js" type="BINDATA" />',
        '      <include name="IDR_AI_PANEL_OLLAMA_PROVIDER_JS" file="resources/side_panel/ai_panel/ollama_provider.js" type="BINDATA" />',
        '      <include name="IDR_AI_PANEL_ANTHROPIC_PROVIDER_JS" file="resources/side_panel/ai_panel/anthropic_provider.js" type="BINDATA" />',
        '      <include name="IDR_AI_PANEL_LOCAL_LLM_PROVIDER_JS" file="resources/side_panel/ai_panel/local_llm_provider.js" type="BINDATA" />',
        '      <include name="IDR_AI_PANEL_PROVIDER_MANAGER_JS" file="resources/side_panel/ai_panel/ai_provider_manager.js" type="BINDATA" />',
        '      <include name="IDR_AI_PANEL_NATIVE_MESSAGING_JS" file="resources/side_panel/ai_panel/native_messaging_helper.js" type="BINDATA" />',
    ]

    lines = content.split('\n')
    insert_idx = None

    # Find the last <include> BINDATA line and add after it
    for i, line in enumerate(lines):
        if '<include name="IDR_' in line and 'BINDATA' in line:
            insert_idx = i

    if insert_idx is None:
        return None

    for j, rl in enumerate(resource_lines):
        lines.insert(insert_idx + 1 + j, rl)

    return '\n'.join(lines)


def main():
    chromium_src = find_chromium_src()

    print("=" * 56)
    print("  AI Panel - Chromium Source Patcher")
    print("=" * 56)
    print(f"\nTarget: {chromium_src}\n")

    results = {'ok': 0, 'skip': 0, 'fail': 0, 'missing': 0}

    patches = [
        ("1/7", "chrome/browser/ui/views/side_panel/side_panel_entry_id.h",
         "kAIPanel", "Side Panel Entry ID",
         patch_side_panel_entry_id),

        ("2/7", "chrome/browser/ui/actions/chrome_action_id.h",
         "kActionSidePanelShowAIPanel", "Chrome Action ID",
         patch_chrome_action_id),

        ("3/7", "chrome/browser/ui/webui/chrome_web_ui_configs.cc",
         "AIPanelUIConfig", "WebUI Config Registration",
         patch_chrome_web_ui_configs),

        ("4a/7", "chrome/browser/ui/browser_window/public/browser_window_features.h",
         "ai_panel_side_panel_coordinator_", "BrowserWindowFeatures Header",
         patch_browser_window_features_header),

        ("4b/7", "chrome/browser/ui/browser_window/internal/browser_window_features.cc",
         "ai_panel_side_panel_coordinator_", "BrowserWindowFeatures Impl",
         patch_browser_window_features_cc),

        ("5/7", "chrome/browser/ui/views/side_panel/side_panel_util.cc",
         "ai_panel_side_panel_coordinator", "Side Panel Util Registration",
         patch_side_panel_util),

        ("6/7", "chrome/browser/ui/views/side_panel/BUILD.gn",
         "ai_panel:ai_panel_side_panel", "Side Panel BUILD.gn",
         patch_side_panel_build_gn),

        ("7/7", "chrome/browser/browser_resources.grd",
         "IDR_AI_PANEL_HTML", "Browser Resources GRD",
         patch_browser_resources_grd),
    ]

    for step, rel_path, marker, desc, patch_fn in patches:
        print(f"[{step}] {desc}...")
        result = patch_file(chromium_src, rel_path, marker, desc, patch_fn)
        results[result] += 1

    print(f"\n{'=' * 56}")
    print(f"  Results: {results['ok']} patched, {results['skip']} skipped, "
          f"{results['fail']} failed, {results['missing']} missing")
    print(f"{'=' * 56}")

    if results['fail'] > 0:
        print("\nSome patches could not find anchor patterns in the Chromium source.")
        print("This may happen if the Chromium version has changed significantly.")
        print("Apply failed patches manually (see CHROMIUM_INTEGRATION.md).")
        sys.exit(1)
    elif results['missing'] > 0:
        print("\nSome Chromium source files were not found.")
        print("Make sure the Chromium source tree is complete at:")
        print(f"  {chromium_src}")
        sys.exit(1)
    else:
        print("\nAll patches applied successfully!")


if __name__ == '__main__':
    main()
