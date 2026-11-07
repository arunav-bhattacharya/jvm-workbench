package workbench.patterns.l08

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.patterns.l08.LedgerCommand.Deposit
import workbench.patterns.l08.LedgerCommand.Withdraw

@OptIn(ExperimentalCoroutinesApi::class)
class ObserverCommandTest {

    // ---- observer ----

    @Test
    fun `listeners hear every posting in order until they close their handle`() = runTest {
        val ledger = ObservableLedger()
        val heard = mutableListOf<Posted>()
        val handle = ledger.subscribe { heard += it }
        ledger.post("acc-1", 450)
        ledger.post("acc-1", 450)
        handle.close()
        ledger.post("acc-1", 900)
        assertThat(heard).containsExactly(Posted("acc-1", 450), Posted("acc-1", 450))
    }

    @Test
    fun `a listener that throws neither stops the others nor fails the posting`() = runTest {
        val ledger = ObservableLedger()
        val heard = mutableListOf<String>()
        ledger.subscribe { heard += "first" }
        ledger.subscribe { throw IllegalStateException("analytics is down") }
        ledger.subscribe { heard += "third" }
        ledger.post("acc-1", 450)
        assertThat(heard).containsExactly("first", "third")
        assertThat(ledger.balance.value).isEqualTo(450L)
    }

    @Test
    fun `a listener may unsubscribe itself while it is being called`() = runTest {
        val ledger = ObservableLedger()
        val heard = mutableListOf<Long>()
        lateinit var oneShot: AutoCloseable
        oneShot = ledger.subscribe { heard += it.amountMinor; oneShot.close() }
        ledger.subscribe { heard += it.amountMinor * 10 }
        ledger.post("acc-1", 1)
        ledger.post("acc-1", 2)
        assertThat(heard).containsExactly(1L, 10L, 20L)
    }

    @Test
    fun `a flow collector gets every posting, even two equal ones in a row`() = runTest {
        val ledger = ObservableLedger()
        val seen = mutableListOf<Posted>()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { ledger.events.toList(seen) }
        ledger.post("acc-1", 450)
        ledger.post("acc-1", 450)
        ledger.post("acc-2", -900)
        assertThat(seen).containsExactly(Posted("acc-1", 450), Posted("acc-1", 450), Posted("acc-2", -900))
    }

    @Test
    fun `balance starts at zero, holds the running total, and gives late collectors the latest value`() = runTest {
        val ledger = ObservableLedger()
        assertThat(ledger.balance.value).isEqualTo(0L)
        ledger.post("acc-1", 450)
        ledger.post("acc-2", 1_000)
        ledger.post("acc-1", -200)
        assertThat(ledger.balance.value).isEqualTo(1_250L)
        assertThat(ledger.balance.first()).isEqualTo(1_250L)
    }

    // ---- command ----

    @Test
    fun `a failing command changes nothing and cannot be undone`() {
        val account = Account("acc-1")
        val stack = CommandStack(account)
        stack.run(Deposit(100))
        stack.run(Withdraw(30))
        assertThatThrownBy { stack.run(Withdraw(1_000)) }
            .isInstanceOf(IllegalStateException::class.java)
            .hasMessage("insufficient funds")
        assertThat(account.balanceMinor).isEqualTo(70)
        assertThat(stack.undoable).containsExactly(Withdraw(30), Deposit(100))
    }

    @Test
    fun `undo walks back one command at a time and says when there is nothing left`() {
        val account = Account("acc-1")
        val stack = CommandStack(account)
        stack.run(Deposit(100))
        stack.run(Withdraw(30))
        assertThat(stack.undo()).isTrue()
        assertThat(account.balanceMinor).isEqualTo(100)
        assertThat(stack.undo()).isTrue()
        assertThat(account.balanceMinor).isEqualTo(0)
        assertThat(stack.undo()).isFalse()
        assertThat(stack.undoable).isEmpty()
    }

    @Test
    fun `redo applies undone commands again, and a new command clears the redo history`() {
        val account = Account("acc-1")
        val stack = CommandStack(account)
        stack.run(Deposit(100))
        stack.run(Withdraw(30))
        stack.undo()
        assertThat(stack.redo()).isTrue()
        assertThat(account.balanceMinor).isEqualTo(70)
        assertThat(stack.redo()).isFalse()

        stack.undo()
        stack.run(Deposit(5))
        assertThat(stack.redo()).`as`("redo after a new command").isFalse()
        assertThat(account.balanceMinor).isEqualTo(105)
        assertThat(stack.undoable).containsExactly(Deposit(5), Deposit(100))
    }
}
