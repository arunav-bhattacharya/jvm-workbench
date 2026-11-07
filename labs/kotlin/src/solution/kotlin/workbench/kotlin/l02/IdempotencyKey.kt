package workbench.kotlin.l02

/**
 * The key a client sends so that a retried request is charged once. At run time it is a String.
 */
@JvmInline
value class IdempotencyKey(val value: String) {
    init {
        require(value.length in 8..64) { "idempotency key must be 8 to 64 characters, was ${value.length}" }
        require(value.all { it.isLetterOrDigit() && it.code < 128 || it == '-' || it == '_' }) {
            "idempotency key may only contain letters, digits, '-' and '_': $value"
        }
    }
}
