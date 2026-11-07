package workbench.bytecode.l02

import java.io.IOException

class Wallet(val owner: String) {
    var balanceMinor: Long = 0
        private set                        // 4. getter only: kotlinc emits no setter method

    var isFrozen: Boolean = false          // 5. a property named isX gets isX() and setX()

    @JvmOverloads                          // 3. also emit deposit(long) that fills in the default
    fun deposit(amountMinor: Long, currency: String = "EUR"): Long {
        check(!isFrozen) { "wallet of $owner is frozen" }
        require(currency == "EUR") { "only EUR wallets: $currency" }
        balanceMinor += amountMinor
        return balanceMinor
    }

    @Throws(IOException::class)            // 6. write `throws IOException` into the method, for javac
    fun exportCsv(out: Appendable) {
        if (isFrozen) throw IOException("export blocked: wallet of $owner is frozen")
        out.append("$owner,$balanceMinor\n")
    }

    companion object {
        const val MAX_BALANCE_MINOR = 10_000_000L   // 1. public static final long on Wallet

        @JvmStatic                                  // 2. a static Wallet.open, not only Companion.open
        fun open(owner: String): Wallet = Wallet(owner)
    }
}
