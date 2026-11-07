package workbench.kotlin.l02

/** "EUR 19.99". The JVM name is receiptLine-<hash>(long): Kotlin callers only. */
fun receiptLine(amount: Money): String = "EUR $amount"

/**
 * The same line for Java callers. @JvmName removes the hash, so Java can call
 * ReceiptsKt.receiptLineForJava(1999L). Java passes a raw long that never went through Money's init,
 * so validate again: Money(amount.cents) runs the init block.
 */
@JvmName("receiptLineForJava")
fun receiptLineJava(amount: Money): String = receiptLine(Money(amount.cents))

/** Returns Money, so Java receives a plain long. Top-level functions are mangled only for value-class parameters. */
fun parseAmount(text: String): Money = Money.parse(text)
