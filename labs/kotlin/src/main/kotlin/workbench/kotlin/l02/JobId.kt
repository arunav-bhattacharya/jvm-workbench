package workbench.kotlin.l02

/**
 * The id the shop's website gives a print job, such as "job-2026-0042". At run time it is a String.
 *
 * TODO 6: add an init block. An id is 8 to 64 characters long and uses only ASCII letters, digits,
 * '-' and '_'. Anything else throws IllegalArgumentException.
 */
@JvmInline
value class JobId(val value: String)
