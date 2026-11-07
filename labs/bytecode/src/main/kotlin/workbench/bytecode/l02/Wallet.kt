package workbench.bytecode.l02

import java.io.IOException

/**
 * A wallet that the Java side of the payments team calls. The Kotlin code works, but the
 * JVM shape kotlinc produces is wrong for the Java callers. The tests read that shape with
 * reflection, the same members `javap -p` lists. Change ONLY annotations, modifiers and the
 * property name so that Java can:
 *
 * 1. read `Wallet.MAX_BALANCE_MINOR` as a static field;
 * 2. call `Wallet.open("ana")` as a static method;
 * 3. call `wallet.deposit(1_250)` without passing the currency;
 * 4. read `getBalanceMinor()` but find no public `setBalanceMinor`;
 * 5. call `wallet.isFrozen()` and `wallet.setFrozen(true)`;
 * 6. catch the `IOException` that `exportCsv` can throw.
 *
 * Run `javap -p` on build/classes/kotlin/main/workbench/bytecode/l02/Wallet.class before and after.
 */
class Wallet(val owner: String) {
    var balanceMinor: Long = 0

    var frozen: Boolean = false

    fun deposit(amountMinor: Long, currency: String = "EUR"): Long {
        check(!frozen) { "wallet of $owner is frozen" }
        require(currency == "EUR") { "only EUR wallets: $currency" }
        balanceMinor += amountMinor
        return balanceMinor
    }

    fun exportCsv(out: Appendable) {
        if (frozen) throw IOException("export blocked: wallet of $owner is frozen")
        out.append("$owner,$balanceMinor\n")
    }

    companion object {
        val MAX_BALANCE_MINOR = 10_000_000L

        fun open(owner: String): Wallet = Wallet(owner)
    }
}
