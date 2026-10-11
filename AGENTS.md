# Agent Guidelines for `microdlms`

This document outlines architecture principles, operational standards, hardware constraints, and testing patterns for AI agents developing or maintaining `microdlms`.

---

## 1. Project Overview & Identity

`microdlms` is an MIT-licensed, zero-core-dependency Python 3.14+ library for read-only DLMS/COSEM utility meter communication.

### Role & Ecosystem
- **Lightweight Alternative**: Designed for Home Assistant and standalone IoT metering systems.
- **Permissive Licensing**: `microdlms` provides an MIT-licensed library implementing the required read-only DLMS subset, suitable for open-source integration.
- **Transport Independence**: Core protocol codecs and state machines operate sans-I/O. Serial/socket I/O is segregated into `microdlms.client` via [`serialx`](https://github.com/home-assistant-libs/serialx), supporting standard serial ports (`/dev/ttyUSB*`, `COM*`), network URLs (`socket://`, `tcp://`), and ESPHome `serial_proxy` bridges.

---

## 2. Architectural Rules & Design Principles

### 2.1 Sans-I/O Purity in Core
- **Zero I/O in Core**: Modules `microdlms.hdlc`, `microdlms.axdr`, `microdlms.apdu`, `microdlms.obis`, `microdlms.types`, and `microdlms.session` must remain **100% sans-I/O**.
- **No I/O Imports**: Never import `socket`, `asyncio`, `serial`, `serialx`, `urllib`, or any networking libraries in core modules.
- **State Machine Pattern**: The session engine (`DlmsSession`) operates strictly on in-memory buffers:
  - Ingestion: `receive_bytes(data: bytes) -> list[SessionEvent]`
  - Outbound data: `data_to_send() -> bytes`
- **I/O Isolation**: All async I/O, timeouts, task orchestration, and socket management reside exclusively in `microdlms.client.AsyncMeterClient`.

### 2.2 Specification-Driven Design
- **Open Standards**: Base protocol implementations on official open DLMS Blue Book and Green Book specifications.
- **Test Vectors**: Validate behavior against verified physical meter frame captures in `tests/meter_fixtures.py`.

---

## 3. Git & Operational Conventions

### 3.1 Commit Guidelines
- **Commit Message Prefix**: Always prefix agent-generated commits with `[ai]` (e.g., `[ai] Support multi-frame A-XDR structures.`).
- **Commit Format**: Keep commit messages concise (under 50 characters including prefix) and end with a full stop (`.`).
- **Branching**: Conduct feature and bugfix work on dedicated branches (`feature/<name>` or `fix/<name>`). Never commit experimental scaffolding directly to the main branch.

### 3.2 Code Hygiene Tools
Before submitting changes, all checks must pass cleanly with zero errors:

```bash
# Code formatting and linting
uv run ruff check
uv run ruff format --check

# Strict static type checking
uv run mypy src tests

# Cognitive complexity verification (max allowed: 15)
uv run complexipy .

# Spelling verification
uv run codespell

# Test suite execution with coverage enforcement
uv run pytest
```

> **Note on Pytest Plugins**: If your local environment has third-party pytest plugins installed (such as `pytest-homeassistant-custom-component` or `pytest-socket`), they may interfere with test execution. You can disable them by adding `-p no:homeassistant -p no:socket`:
> ```bash
> uv run pytest -p no:homeassistant -p no:socket
> ```


When using `prek` (Astral's Git hook manager):
```bash
prek run --all-files
```

### 3.3 Code Style & Naming Conventions
- **Self-Descriptive Naming**: Ensure human-readable, self-descriptive names for variables, parameters, and attributes across both codebase and test suites. Avoid terse or cryptic abbreviations (e.g., use `position` over `pos`, `message` over `msg`, `frame_1` over `f1`).

---

## 4. Hardware Realities & DLMS Communication

### 4.1 Optical Probe Timing & Constraints
- **Low Baud Rate**: Optical IR utility meter communication runs predominantly at 9600 baud (8N1).
- **Latency**: Each attribute read request-response exchange takes between 0.5 and 1.5 seconds over physical optical links.
- **Exclusive Access**: Serial connections and optical probes are strictly exclusive. Only one active session may use the serial link or TCP socket proxy at a time.
- **Frame Slicing**: Optical links frequently fragment or concatenate byte streams. Codecs must handle partial frames across multiple chunk arrivals and cleanly identify frame boundaries (`0x7E` framing flags).
- **Optical Echo Filtering**: Half-duplex optical probes often reflect transmitted TX bytes back to the receiver (RX echo). `AsyncMeterClient(echo_filter=True)` provides prefix-based echo filtering:
  - Buffers transmitted frames in `_pending_echo`.
  - Discards matching echo prefixes from incoming chunks, logging discarded counts at `logging.DEBUG` level.
  - Clears `_pending_echo` on byte mismatches, echo exhaustion, disconnects, reconnects, or retries to avoid dropping valid meter response data.

### 4.2 Sequence Tracking & Protocol Fields
- **HDLC Sequence Counters**: $N(S)$ (send sequence number) and $N(R)$ (receive sequence number) are cyclic counters modulo 8 ($0..7$).
- **DLMS Invoke IDs**: DLMS invocation identifiers are cyclic counters modulo 16 ($0..15$).
- **LLC Sublayer**: DLMS frames over HDLC I-frames use LLC encapsulation:
  - Client LLC header: `0xE6 0xE6 0x00`
  - Server LLC header: `0xE6 0xE7 0x00`
- **Dual Error Model**:
  - The sans-I/O `DlmsSession` yields typed events (`AssociationRejectedEvent`, `GetAccessErrorEvent`, `ProtocolErrorEvent`) rather than raising exceptions, maintaining continuous byte consumption.
  - The async `AsyncMeterClient` converts error events into appropriate Python exceptions:
    - `CommunicationError`: physical link, timeout, or framing errors.
    - `AuthenticationError`: LLS password or association rejections.
    - `DataAccessError`: COSEM data access errors (carrying `DataAccessResult`).

---

## 5. Testing & Coverage Rules

### 5.1 Simulated & Mocked I/O
- **No Real Hardware or Network I/O**: Tests must never open real physical serial ports or external network connections.
- **Mock Transport**: Test client interactions using mock readers/writers or mocked `serialx.open_serial_connection` factories.
- **Deterministic Sans-I/O Testing**: Primary protocol logic must be tested by feeding synthetic or captured byte vectors directly to `DlmsSession.receive_bytes()`.

### 5.2 Test Vectors & Replay Verification
- **Physical Meter Fixtures**: The repository includes physical meter captures in `tests/meter_fixtures.py` and `tests/meter_data.json` covering:
  - HDLC Connection (`SNRM` $\rightarrow$ `UA`)
  - AARQ Application Association with LLS password authentication
  - Authentication failure responses (`REJECTED_PERMANENT`, diagnostic `13`)
  - Logical Device Name (`0.0.42.0.0.255`, attr 2)
  - Meter Serial Number (`0.0.96.1.0.255`, attr 2)
  - Voltage, current, power readings and `ScalerUnit` structures
  - Error responses (`OBJECT_UNDEFINED` for non-existent OBIS or attribute)
  - Disconnect sequence (`DISC` $\rightarrow$ `UA`)
- `tests/test_fixture_replay.py` must continually validate all 46 captured frame exchanges.

### 5.3 Coverage Enforcement
- **Minimum 95% Coverage**: Branch and statement coverage across `src/microdlms/` must remain at or above 95% at all times.
- Pytest enforces this via:
  ```bash
  uv run pytest --cov=microdlms --cov-fail-under=95
  ```

