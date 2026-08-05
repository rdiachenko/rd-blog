# Parse, don't validate: runnable code

Companion code for [Parse, Don't Validate, in Rust](https://rdiachenko.com/posts/rust/parse-dont-validate/).
Every snippet in the post is assembled here so it actually compiles and runs.

## Rust

```bash
cd rust
cargo test    # 15 tests: every claim in the post as an assertion
cargo run     # reproduces the shotgun-parsing output from the post
```

`cargo run` prints exactly the console block in the post:

```text
shotgun     -> rejected with ZeroReplicas
  deployments : ["checkout-api"]
  traffic     : ["production -> checkout-api"]
  audit       : []

parse-first -> rejected with ZeroReplicas
  deployments : []
  traffic     : []
  audit       : []
```

| Module | Post section |
|---|---|
| `request.rs` | The same code in Rust |
| `validate_first.rs` | The same code in Rust (plus the `should_panic` test) |
| `domain.rs` | Refining the type, Parsing at the boundary |
| `parse_first.rs` | Refining the type |
| `illegal_states.rs` | Removing invalid states |
| `shotgun.rs` | Shotgun parsing |
| `derive_trap.rs` | The derive that skips your constructor |

## Java

```bash
cd java
mvn test      # 4 tests
mvn spring-boot:run   # POST http://localhost:8080/deploys
```

```bash
curl -X POST localhost:8080/deploys -H 'Content-Type: application/json' \
  -d '{"service":"checkout-api","environment":"production","replicas":3}'   # 202
curl -X POST localhost:8080/deploys -H 'Content-Type: application/json' \
  -d '{"service":"Not A Service","environment":"qa","replicas":0}'          # 400
```

## One thing the post leaves implicit

**`is_service_name` / `is_environment`** are called by `validate` and
`deploy_shotgun`. Their names say what they do, so the post doesn't show their
bodies; this project has to, and they live in `validate_first.rs`. Worth a look:
they duplicate the checks inside `ServiceName::parse` and `Environment::parse`,
which is exactly the duplication that parsing removes.

Everything else here uses only standard Jakarta Bean Validation. There is no
built-in "value must be one of this set" constraint (`@ValidEnum` is an open
proposal, [jakartaee/validation#229](https://github.com/jakartaee/validation/issues/229),
and Hibernate Validator adds nothing equivalent), so `environment` uses
`@Pattern(regexp = "dev|staging|production")`. No custom constraint, and
`environment` stays a `String`, which is the point: validation leaves the type
exactly as it found it.

## What each side demonstrates

The Rust tests show that the illegal states are unreachable: `Replicas::new(0)`
fails, `Deploy::try_from` rejects before any effect runs, and
`serde_json::from_str::<Deploy>` never yields a value that skipped the
constructor.

The Java tests show the opposite shape. `successfulValidationProducesNothing`
asserts that a passing `validator.validate(req)` returns an empty set, and
`validationDoesNotChangeTheValueOrItsType` asserts the request is the same
object of the same type afterwards. Nothing is available to pass downstream as
evidence that the check happened.
