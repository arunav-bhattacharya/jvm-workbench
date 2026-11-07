package workbench.patterns.l08

class Account(val id: String) {
    var balanceMinor: Long = 0
}

sealed interface LedgerCommand {
    fun apply(account: Account)
    fun undo(account: Account)

    data class Deposit(val amountMinor: Long) : LedgerCommand {
        override fun apply(account: Account) {
            account.balanceMinor += amountMinor
        }

        override fun undo(account: Account) {
            account.balanceMinor -= amountMinor
        }
    }

    data class Withdraw(val amountMinor: Long) : LedgerCommand {
        override fun apply(account: Account) {
            check(account.balanceMinor >= amountMinor) { "insufficient funds" }   // throws before changing anything
            account.balanceMinor -= amountMinor
        }

        override fun undo(account: Account) {
            account.balanceMinor += amountMinor
        }
    }
}

class CommandStack(private val account: Account) {
    private val done = ArrayDeque<LedgerCommand>()      // most recent first
    private val undone = ArrayDeque<LedgerCommand>()    // most recently undone first

    val undoable: List<LedgerCommand>
        get() = done.toList()

    fun run(cmd: LedgerCommand) {
        cmd.apply(account)          // 1. apply first: if it throws, nothing below runs
        done.addFirst(cmd)          // 2. record only after success
        undone.clear()              // 3. a new action ends the redo history
    }

    fun undo(): Boolean {
        val cmd = done.removeFirstOrNull() ?: return false
        cmd.undo(account)
        undone.addFirst(cmd)
        return true
    }

    fun redo(): Boolean {
        val cmd = undone.removeFirstOrNull() ?: return false
        cmd.apply(account)
        done.addFirst(cmd)
        return true
    }
}
