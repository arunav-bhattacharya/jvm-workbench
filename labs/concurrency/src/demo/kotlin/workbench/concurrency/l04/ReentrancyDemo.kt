package workbench.concurrency.l04

// A synchronized method calls another synchronized method on the same object.
open class SavingsAccount {
    private var balanceCents = 10_000L

    @Synchronized open fun withdraw(cents: Long) {
        println("withdraw: holds the lock? ${Thread.holdsLock(this)}")
        if (canCover(cents)) balanceCents -= cents    // takes the same lock again
    }

    @Synchronized fun canCover(cents: Long): Boolean {
        println("canCover: holds the lock? ${Thread.holdsLock(this)}")
        return balanceCents >= cents
    }
}

class AuditedSavingsAccount : SavingsAccount() {
    @Synchronized override fun withdraw(cents: Long) {
        println("audit: about to withdraw $cents")
        super.withdraw(cents)                        // and again, through super
    }
}

fun main() {
    AuditedSavingsAccount().withdraw(2_500)
    println("done: no thread waited for a lock it already held")
}
