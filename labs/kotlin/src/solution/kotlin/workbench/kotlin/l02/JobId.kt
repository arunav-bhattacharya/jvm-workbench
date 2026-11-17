package workbench.kotlin.l02

/**
 * The id the shop's website gives a print job, such as "job-2026-0042". At run time it is a String.
 */
@JvmInline
value class JobId(val value: String) {
    init {
        require(value.length in 8..64) { "job id must be 8 to 64 characters, was ${value.length}" }
        require(value.all { it.isLetterOrDigit() && it.code < 128 || it == '-' || it == '_' }) {
            "job id may only contain letters, digits, '-' and '_': $value"
        }
    }
}
