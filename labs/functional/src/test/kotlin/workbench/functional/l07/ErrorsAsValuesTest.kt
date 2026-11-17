package workbench.functional.l07

import arrow.core.Either
import arrow.core.left
import arrow.core.nonEmptyListOf
import arrow.core.right
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class)
class ErrorsAsValuesTest {

    private val good = IngredientForm("strong flour", 500, "g", "the blue bag, please")

    // ---- validate: collect every error ----

    @Test
    fun `validate accepts a good line`() {
        assertThat(validate(good)).isEqualTo(Ingredient("strong flour", 500, "g", "the blue bag, please").right())
    }

    @Test
    fun `validate reports one broken rule`() {
        assertThat(validate(good.copy(unit = "oz")))
            .isEqualTo(nonEmptyListOf<KitchenError>(KitchenError.UnsupportedUnit("oz")).left())
    }

    @Test
    fun `validate reports every broken rule at once, in order`() {
        val bad = IngredientForm("fl0ur", -5, "oz", "x".repeat(40))
        assertThat(validate(bad)).isEqualTo(
            nonEmptyListOf(
                KitchenError.InvalidName("fl0ur"),
                KitchenError.InvalidAmount(-5),
                KitchenError.UnsupportedUnit("oz"),
                KitchenError.NoteTooLong(40),
            ).left()
        )
    }

    @Test
    fun `validate checks a blank name and the note length`() {
        assertThat(validate(good.copy(name = " ")))
            .isEqualTo(nonEmptyListOf<KitchenError>(KitchenError.InvalidName(" ")).left())
        assertThat(validate(good.copy(note = "n".repeat(35))).isRight()).`as`("35 characters is allowed").isTrue()
    }

    // ---- order: fail fast ----

    private val flour = Ingredient("strong flour", 500, "g", "")

    private class FakeShop(
        private val reserve: Either<KitchenError, String> = "B-1".right(),
        private val minutes: Int = 45,
        private val book: Either<KitchenError, String> = "S-1".right(),
    ) : Shop {
        val calls = mutableListOf<String>()
        override fun reserve(ingredient: Ingredient) = reserve.also { calls += "reserve" }
        override fun deliveryMinutes(basketId: String) = minutes.also { calls += "deliveryMinutes" }
        override fun book(basketId: String) = book.also { calls += "book" }
    }

    @Test
    fun `order returns a delivery when every step succeeds`() {
        val shop = FakeShop()
        assertThat(order(flour, shop)).isEqualTo(Delivery("B-1", "S-1").right())
        assertThat(shop.calls).containsExactly("reserve", "deliveryMinutes", "book")
    }

    @Test
    fun `order stops when the shop is out of stock`() {
        val shop = FakeShop(reserve = KitchenError.OutOfStock.left())
        assertThat(order(flour, shop)).isEqualTo(KitchenError.OutOfStock.left())
        assertThat(shop.calls).containsExactly("reserve")
    }

    @Test
    fun `order refuses a late delivery and never books it`() {
        val shop = FakeShop(minutes = 150)
        assertThat(order(flour, shop)).isEqualTo(KitchenError.TooLate(150).left())
        assertThat(shop.calls).containsExactly("reserve", "deliveryMinutes")
    }

    @Test
    fun `order treats the limit itself as too late`() {
        assertThat(order(flour, FakeShop(minutes = LATEST_MINUTES))).isEqualTo(KitchenError.TooLate(120).left())
        assertThat(order(flour, FakeShop(minutes = LATEST_MINUTES - 1)).isRight()).isTrue()
    }

    @Test
    fun `order returns a failed booking as it is`() {
        val shop = FakeShop(book = KitchenError.ShopClosed.left())
        assertThat(order(flour, shop)).isEqualTo(KitchenError.ShopClosed.left())
    }

    // ---- runCatchingCancellable ----

    @Test
    fun `runCatchingCancellable wraps a value`() = runTest {
        assertThat(runCatchingCancellable { delay(100); "basket-1" }).isEqualTo(Result.success("basket-1"))
    }

    @Test
    fun `runCatchingCancellable wraps an ordinary exception`() = runTest {
        val result = runCatchingCancellable<String> { delay(100); throw IOException("shop timeout") }
        assertThat(result.exceptionOrNull()).isInstanceOf(IOException::class.java).hasMessage("shop timeout")
    }

    @Test
    fun `a cancelled caller does not carry on after runCatchingCancellable`() = runTest {
        val placed = mutableListOf<String>()
        val shopping = launch {
            val result = runCatchingCancellable { delay(1_000); "basket-1" }
            placed += "placed the order ($result)"   // must never run once the shopping is cancelled
        }
        advanceTimeBy(50)
        shopping.cancelAndJoin()
        assertThat(placed).`as`("orders placed after the cancel").isEmpty()
        assertThat(shopping.isCancelled).isTrue()
    }
}
