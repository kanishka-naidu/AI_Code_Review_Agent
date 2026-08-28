# Insecure Deserialization Prevention

## Overview
Insecure deserialization occurs when an application deserializes untrusted data without proper validation. This can lead to remote code execution, denial of service, or data tampering.

**OWASP Reference:** A08:2021 – Software and Data Integrity Failures

## Primary Defense: Avoid Deserializing Untrusted Data
The safest approach is to avoid deserializing data from untrusted sources entirely. Use safe data interchange formats like JSON or XML with strict validation.

## Python: Avoid pickle
The `pickle` module can execute arbitrary code during deserialization. Never use it on untrusted data.

```python
# VULNERABLE — pickle can execute arbitrary code
import pickle
data = pickle.loads(untrusted_bytes)

# SAFE — use JSON
import json
data = json.loads(untrusted_string)
```

## Java: Validate ObjectInputStream
Java's native deserialization is dangerous. If you must use it, implement a filter or allowlist.

```java
// VULNERABLE
ObjectInputStream ois = new ObjectInputStream(inputStream);
Object obj = ois.readObject();

// SAFER — use a filter (Java 9+)
ObjectInputFilter filter = ObjectInputFilter.Config.createFilter("com.example.*;java.base/*;!*");
ObjectInputStream ois = new ObjectInputStream(inputStream);
ois.setObjectInputFilter(filter);
Object obj = ois.readObject();
```

## Defense 2: Use Allowlists
If deserialization is required, only allow known-safe classes.

- Maintain an explicit allowlist of permitted classes.
- Reject any class not on the allowlist.
- Never use a denylist approach, as it is incomplete.

## Defense 3: Validate After Deserialization
After deserialization, validate the resulting object's state.

- Check that required fields are present and have valid values.
- Verify the object is of the expected type.
- Reject objects that fail validation.

## Defense 4: Use Safe Alternatives
Prefer safe data formats over native serialization.

- Use JSON with a strict schema validator.
- Use XML with a secure parser that disables external entities (XXE protection).
- Use protocol buffers or other safe binary formats.

## Detection Indicators
- Use of `pickle.loads()` or `pickle.load()` on untrusted data
- `ObjectInputStream.readObject()` without a filter
- Deserialization of data from user-controlled sources
- Missing validation after deserialization
- Use of native serialization for data interchange