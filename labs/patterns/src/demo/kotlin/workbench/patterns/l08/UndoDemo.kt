package workbench.patterns.l08

// Commands as data classes, an undo log, and the one rule that keeps undo honest.

class Wallet { var balance = 0L }

sealed interface WalletCommand {
    fun apply(w: Wallet)
    fun undo(w: Wallet)

    data class Deposit(val amount: Long) : WalletCommand {
        override fun apply(w: Wallet) { w.balance += amount }
        override fun undo(w: Wallet) { w.balance -= amount }
    }

    data class Withdraw(val amount: Long) : WalletCommand {
        override fun apply(w: Wallet) {
            check(w.balance >= amount) { "insufficient funds" }
            w.balance -= amount
        }
        override fun undo(w: Wallet) { w.balance += amount }
    }
}

class CommandLog {
    val history = ArrayDeque<WalletCommand>()

    fun run(c: WalletCommand, w: Wallet) {
        c.apply(w)                   // 1. apply first
        history.addFirst(c)          // 2. record only after it worked
    }

    fun undoLast(w: Wallet) {
        history.removeFirstOrNull()?.undo(w)
    }
}

fun main() {
    val wallet = Wallet()
    val log = CommandLog()
    log.run(WalletCommand.Deposit(100), wallet)
    log.run(WalletCommand.Withdraw(30), wallet)
    try {
        log.run(WalletCommand.Withdraw(1_000), wallet)
    } catch (e: IllegalStateException) {
        println("rejected: ${e.message}")
    }
    println("balance ${wallet.balance}, history ${log.history}")
    log.undoLast(wallet)
    println("after one undo: balance ${wallet.balance}, history ${log.history}")
}
