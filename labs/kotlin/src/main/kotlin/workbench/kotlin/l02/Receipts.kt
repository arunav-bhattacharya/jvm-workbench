package workbench.kotlin.l02

/** "EUR 19.99". Kotlin callers only: its JVM name is receiptLine-<hash>(long), which javac can't call. */
fun receiptLine(amount: Money): String = TODO("\"EUR \$amount\"")

/*
 * TODO 7: an older Java module needs the same line. Add a function here that Java can call as
 * ReceiptsKt.receiptLineForJava(1999L) and that returns "EUR 19.99".
 *  - Its parameter is still a Money. Give it the JVM name receiptLineForJava with one annotation.
 *  - Java hands over a raw long that never went through Money's init. Make -500L throw
 *    IllegalArgumentException anyway.
 */

/** Returns Money, so Java receives a plain long. Finished: it works once Money.parse does. */
fun parseAmount(text: String): Money = Money.parse(text)
