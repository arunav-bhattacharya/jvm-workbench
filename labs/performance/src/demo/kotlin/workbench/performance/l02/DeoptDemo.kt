package workbench.performance.l02

// Kotlin twin of DeoptDemo.java: card charges only, then a refund appears, then SEPA and wallet payments.
// Run it: a second JVM starts with -XX:+PrintCompilation and -Xlog:deoptimization=debug.

interface PaymentMethod { fun feeCents(amountCents: Long): Long }
class CardFee(private val bps: Long) : PaymentMethod { override fun feeCents(amountCents: Long) = amountCents * bps / 10_000 }
class SepaFee(private val flat: Long) : PaymentMethod { override fun feeCents(amountCents: Long) = flat }
class WalletFee(private val bps: Long, private val flat: Long) : PaymentMethod {
    override fun feeCents(amountCents: Long) = amountCents * bps / 10_000 + flat
}

fun settle(methods: Array<PaymentMethod>, amounts: LongArray, refund: BooleanArray): Long {
    var net = 0L
    for (i in amounts.indices) {
        val fee = methods[i].feeCents(amounts[i])   // call site: which types has it seen?
        if (refund[i]) net -= amounts[i]            // branch: has it ever been taken?
        else net += amounts[i] - fee
    }
    return net
}

private fun work() {
    val n = 1_000
    val methods = Array<PaymentMethod>(n) { CardFee(290) }
    val amounts = LongArray(n) { 1_000L + it }
    val refund = BooleanArray(n)
    var total = 0L

    println("phase 1: card charges only")
    repeat(3_000) { total += settle(methods, amounts, refund) }

    println("phase 2: one refund per batch")
    refund[500] = true
    repeat(3_000) { total += settle(methods, amounts, refund) }

    println("phase 3: SEPA and wallet payments arrive")
    for (i in 0 until n step 3) methods[i] = SepaFee(35)
    for (i in 1 until n step 3) methods[i] = WalletFee(150, 10)
    repeat(3_000) { total += settle(methods, amounts, refund) }
    println("done, checksum $total")
}

fun main(args: Array<String>) {
    if (args.firstOrNull() == "child") return work()
    val java = ProcessHandle.current().info().command().orElse("java")
    val p = ProcessBuilder(java, "-XX:+PrintCompilation", "-Xlog:deoptimization=debug",
        "-cp", System.getProperty("java.class.path"), "workbench.performance.l02.DeoptDemoKt", "child")
        .redirectErrorStream(true).start()
    p.inputReader().useLines { lines ->
        lines.filter { "DeoptDemoKt::settle" in it || "DeoptDemoKt.settle" in it || it.startsWith("phase") || it.startsWith("done") }
            .map { it.replace(Regex(" pc=.*"), "") }   // drop machine addresses
            .forEach(::println)
    }
    p.waitFor()
}
