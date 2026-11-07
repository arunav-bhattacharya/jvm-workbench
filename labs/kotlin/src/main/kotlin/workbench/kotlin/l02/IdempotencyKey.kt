package workbench.kotlin.l02

/**
 * The key a client sends so that a retried request is charged once. At run time it is a String.
 *
 * TODO 6: add an init block. A key is 8 to 64 characters long and uses only ASCII letters, digits,
 * '-' and '_'. Anything else throws IllegalArgumentException.
 */
@JvmInline
value class IdempotencyKey(val value: String)
