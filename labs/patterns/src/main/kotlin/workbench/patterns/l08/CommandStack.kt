package workbench.patterns.l08

/** A ledger account. Given; don't change it. */
class Account(val id: String) {
    var balanceMinor: Long = 0
}

/** A request to change an account, as a value: it can be stored, logged, queued and undone. */
sealed interface LedgerCommand {
    fun apply(account: Account)
    fun undo(account: Account)

    /** Adds [amountMinor] to the balance. Undo takes it away again. */
    data class Deposit(val amountMinor: Long) : LedgerCommand {
        override fun apply(account: Account) {
            TODO("add the amount")
        }

        override fun undo(account: Account) {
            TODO("take it away again")
        }
    }

    /**
     * Takes [amountMinor] from the balance, or throws IllegalStateException("insufficient funds")
     * and changes nothing if the balance is too low. Undo puts the amount back.
     */
    data class Withdraw(val amountMinor: Long) : LedgerCommand {
        override fun apply(account: Account) {
            TODO("check the balance first, then take the amount")
        }

        override fun undo(account: Account) {
            TODO("put the amount back")
        }
    }
}

/** Runs commands against one account and keeps what it needs for undo and redo. */
class CommandStack(private val account: Account) {

    /** The commands that can be undone, most recent first. */
    val undoable: List<LedgerCommand>
        get() = TODO("a copy of the undo history")

    /**
     * Runs [cmd]. Only a command that succeeded can be undone: one that throws leaves no trace.
     * Running a new command clears the redo history.
     */
    fun run(cmd: LedgerCommand) {
        TODO("apply first, record only after it worked, clear redo")
    }

    /** Undoes the most recent command. Returns false if there is nothing to undo. */
    fun undo(): Boolean = TODO("pop, undo, remember it for redo")

    /** Applies the most recently undone command again. Returns false if there is nothing to redo. */
    fun redo(): Boolean = TODO("pop from redo, apply, push back on the undo history")
}
