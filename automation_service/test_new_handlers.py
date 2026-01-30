#!/usr/bin/env python3
"""Smoke test for new Native Messaging handlers:
   - get_provider_status
   - store_api_key / delete_api_key
   - get_actions (async submit)
   - poll (async poll)
"""
import sys
import struct
import json
import subprocess

SERVICE_EXE = r'A:\browser-ai\automation_service\build\bin\Release\automation_service.exe'


def send_message(message):
    encoded = json.dumps(message).encode('utf-8')
    return struct.pack('@I', len(encoded)) + encoded


def read_message(stream):
    raw = stream.read(4)
    if len(raw) == 0:
        return None
    length = struct.unpack('@I', raw)[0]
    data = stream.read(length).decode('utf-8')
    return json.loads(data)


def test_single(message):
    proc = subprocess.Popen(
        [SERVICE_EXE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    proc.stdin.write(send_message(message))
    proc.stdin.flush()
    proc.stdin.close()
    response = read_message(proc.stdout)
    proc.wait()
    return response


def test_multi(messages):
    """Send multiple messages in one session and read all responses."""
    proc = subprocess.Popen(
        [SERVICE_EXE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for msg in messages:
        proc.stdin.write(send_message(msg))
        proc.stdin.flush()

    proc.stdin.close()

    responses = []
    for _ in messages:
        resp = read_message(proc.stdout)
        if resp is None:
            break
        responses.append(resp)

    proc.wait()
    return responses


def run_test(name, message, checks):
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"{'='*60}")
    print(f"  Send: {json.dumps(message)}")
    response = test_single(message)
    print(f"  Recv: {json.dumps(response, indent=4)}")

    passed = True
    for desc, check_fn in checks:
        ok = check_fn(response)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {desc}")
        if not ok:
            passed = False

    return passed


def main():
    results = []

    # 1. get_provider_status
    results.append(run_test(
        "get_provider_status",
        {"action": "get_provider_status"},
        [
            ("response has success=true", lambda r: r.get("success") is True),
            ("has providers object", lambda r: isinstance(r.get("providers"), dict)),
            ("has openai provider", lambda r: "openai" in r.get("providers", {})),
            ("has anthropic provider", lambda r: "anthropic" in r.get("providers", {})),
            ("has ollama provider", lambda r: "ollama" in r.get("providers", {})),
            ("openai has has_key field", lambda r: "has_key" in r.get("providers", {}).get("openai", {})),
            ("ollama has available field", lambda r: "available" in r.get("providers", {}).get("ollama", {})),
        ]
    ))

    # 2. store_api_key
    results.append(run_test(
        "store_api_key (openai)",
        {"action": "store_api_key", "provider": "openai", "api_key": "sk-test-smoke-12345"},
        [
            ("response has success=true", lambda r: r.get("success") is True),
        ]
    ))

    # 3. verify key was stored
    results.append(run_test(
        "get_provider_status (after store)",
        {"action": "get_provider_status"},
        [
            ("openai now has_key=true", lambda r: r.get("providers", {}).get("openai", {}).get("has_key") is True),
        ]
    ))

    # 4. delete_api_key
    results.append(run_test(
        "delete_api_key (openai)",
        {"action": "delete_api_key", "provider": "openai"},
        [
            ("response has success=true", lambda r: r.get("success") is True),
        ]
    ))

    # 5. verify key was deleted
    results.append(run_test(
        "get_provider_status (after delete)",
        {"action": "get_provider_status"},
        [
            ("openai now has_key=false", lambda r: r.get("providers", {}).get("openai", {}).get("has_key") is False),
        ]
    ))

    # 6. store_api_key validation — bad provider
    results.append(run_test(
        "store_api_key (bad provider)",
        {"action": "store_api_key", "provider": "badprovider", "api_key": "sk-test"},
        [
            ("response has success=false", lambda r: r.get("success") is False),
            ("has error message", lambda r: bool(r.get("error"))),
        ]
    ))

    # 7. get_actions (async submit) — will queue even if Ollama call fails/takes long
    results.append(run_test(
        "get_actions (submit async)",
        {"action": "get_actions", "provider": "ollama", "user_request": "Open Notepad"},
        [
            ("has request_id", lambda r: bool(r.get("request_id"))),
            ("status is queued", lambda r: r.get("status") == "queued"),
        ]
    ))

    # 8. poll — use a fake ID to verify the handler works
    results.append(run_test(
        "poll (unknown request_id)",
        {"action": "poll", "request_id": "nonexistent"},
        [
            ("status is not_found", lambda r: r.get("status") == "not_found"),
        ]
    ))

    # 9. cancel — use a fake ID
    results.append(run_test(
        "cancel (unknown request_id)",
        {"action": "cancel", "request_id": "nonexistent"},
        [
            ("status is not_found", lambda r: r.get("status") == "not_found"),
        ]
    ))

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r)
    failed = total - passed
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed, {failed} failed")
    print(f"{'='*60}")
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
