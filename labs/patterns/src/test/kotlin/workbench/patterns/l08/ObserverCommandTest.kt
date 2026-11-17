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
import workbench.patterns.l08.ShelfCommand.Restock
import workbench.patterns.l08.ShelfCommand.Sell

@OptIn(ExperimentalCoroutinesApi::class)
class ObserverCommandTest {

    // ---- observer ----

    @Test
    fun `listeners hear every order in turn until they close their handle`() = runTest {
        val orders = ObservableOrders()
        val heard = mutableListOf<Ordered>()
        val handle = orders.subscribe { heard += it }
        orders.place("Ana", "rye bread", 1)
        orders.place("Ana", "rye bread", 1)
        handle.close()
        orders.place("Ben", "jam", 2)
        assertThat(heard).containsExactly(Ordered("Ana", "rye bread", 1), Ordered("Ana", "rye bread", 1))
    }

    @Test
    fun `a listener that throws neither stops the others nor fails the order`() = runTest {
        val orders = ObservableOrders()
        val heard = mutableListOf<String>()
        orders.subscribe { heard += "first" }
        orders.subscribe { throw IllegalStateException("the sales chart is down") }
        orders.subscribe { heard += "third" }
        orders.place("Ana", "rye bread", 1)
        assertThat(heard).containsExactly("first", "third")
        assertThat(orders.itemsToday.value).isEqualTo(1)
    }

    @Test
    fun `a listener may unsubscribe itself while it is being called`() = runTest {
        val orders = ObservableOrders()
        val heard = mutableListOf<Int>()
        lateinit var oneShot: AutoCloseable
        oneShot = orders.subscribe { heard += it.quantity; oneShot.close() }
        orders.subscribe { heard += it.quantity * 10 }
        orders.place("Ana", "tea", 1)
        orders.place("Ben", "tea", 2)
        assertThat(heard).containsExactly(1, 10, 20)
    }

    @Test
    fun `a flow collector gets every order, even two equal ones in a row`() = runTest {
        val orders = ObservableOrders()
        val seen = mutableListOf<Ordered>()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { orders.events.toList(seen) }
        orders.place("Ana", "rye bread", 1)
        orders.place("Ana", "rye bread", 1)
        orders.place("Ben", "jam", 2)
        assertThat(seen).containsExactly(Ordered("Ana", "rye bread", 1), Ordered("Ana", "rye bread", 1), Ordered("Ben", "jam", 2))
    }

    @Test
    fun `itemsToday starts at zero, holds the running total, and gives late collectors the latest value`() = runTest {
        val orders = ObservableOrders()
        assertThat(orders.itemsToday.value).isEqualTo(0)
        orders.place("Ana", "rye bread", 1)
        orders.place("Ben", "jam", 4)
        orders.place("Cleo", "tea", 2)
        assertThat(orders.itemsToday.value).isEqualTo(7)
        assertThat(orders.itemsToday.first()).isEqualTo(7)
    }

    // ---- command ----

    @Test
    fun `a failing command changes nothing and cannot be undone`() {
        val shelf = Shelf("rye bread")
        val stack = CommandStack(shelf)
        stack.run(Restock(12))
        stack.run(Sell(5))
        assertThatThrownBy { stack.run(Sell(40)) }
            .isInstanceOf(IllegalStateException::class.java)
            .hasMessage("not enough on the shelf")
        assertThat(shelf.units).isEqualTo(7)
        assertThat(stack.undoable).containsExactly(Sell(5), Restock(12))
    }

    @Test
    fun `undo walks back one command at a time and says when there is nothing left`() {
        val shelf = Shelf("rye bread")
        val stack = CommandStack(shelf)
        stack.run(Restock(12))
        stack.run(Sell(5))
        assertThat(stack.undo()).isTrue()
        assertThat(shelf.units).isEqualTo(12)
        assertThat(stack.undo()).isTrue()
        assertThat(shelf.units).isEqualTo(0)
        assertThat(stack.undo()).isFalse()
        assertThat(stack.undoable).isEmpty()
    }

    @Test
    fun `redo applies undone commands again, and a new command clears the redo history`() {
        val shelf = Shelf("rye bread")
        val stack = CommandStack(shelf)
        stack.run(Restock(12))
        stack.run(Sell(5))
        stack.undo()
        assertThat(stack.redo()).isTrue()
        assertThat(shelf.units).isEqualTo(7)
        assertThat(stack.redo()).isFalse()

        stack.undo()
        stack.run(Restock(1))
        assertThat(stack.redo()).`as`("redo after a new command").isFalse()
        assertThat(shelf.units).isEqualTo(13)
        assertThat(stack.undoable).containsExactly(Restock(1), Restock(12))
    }
}
