# Expected Findings — fixtures/structural_port.sv

| # | file:line            | construct           | severity | category          |
|---|----------------------|---------------------|----------|-------------------|
| 1 | structural_port.sv:4 | `real parameter`    | error    | structural/port   |

Summary: `1 findings: 1 errors, 0 warnings, 0 notes`

(Port-width mismatch at the instance is not line-flaggable by simple pattern
matching; the manifest records only the line-determinable construct.)
