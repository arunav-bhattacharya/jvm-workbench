package workbench.functional.l04.demo

// The sample settlement day shared by the Kotlin demos of this lesson.

enum class Status { SETTLED, PENDING, FAILED }

data class Payment(
    val id: String,
    val merchant: String,
    val amountCents: Long,
    val status: Status,
    val refundCents: Long? = null,
)

val sampleDay = listOf(
    Payment("pay_1", "acme", 1_500, Status.SETTLED),
    Payment("pay_2", "globex", 9_900, Status.PENDING),
    Payment("pay_3", "acme", 2_000, Status.SETTLED, refundCents = 500),
    Payment("pay_4", "initech", 12_000, Status.FAILED),
    Payment("pay_5", "globex", 700, Status.SETTLED),
)
