package workbench.generics.l09

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import kotlin.reflect.typeOf

class CardIndexTest {

    private val gala = Apple("Gala", 180)

    @Test
    fun `get by KClass returns the tool filed under it`() {
        val index = CardIndex()
        val scale = ShopScale("till scale")
        index.register(Scale::class, scale)
        index.register(LabelPrinter::class, PlainLabels())
        assertThat(index.get(Scale::class)).isSameAs(scale)
        assertThat(index.get(LabelPrinter::class).labelFor(gala)).isEqualTo("Gala, 180 g")
    }

    @Test
    fun `reified get finds the tool from the type argument alone`() {
        val index = CardIndex()
        val scale = ShopScale("till scale")
        index.register(Scale::class, scale)
        index.register(LabelPrinter::class, PlainLabels())
        assertThat(Callers.scale(index)).isSameAs(scale)
        assertThat(Callers.labels(index)).isInstanceOf(PlainLabels::class.java)
    }

    @Test
    fun `a later card replaces the earlier one`() {
        val index = CardIndex()
        index.register(Scale::class, ShopScale("till scale"))
        index.register(Scale::class, ShopScale("back-room scale"))
        assertThat(Callers.scale(index).weigh(gala)).isEqualTo("back-room scale: Gala weighs 180 g")
    }

    @Test
    fun `a missing card throws NoSuchElementException naming the class`() {
        val index = CardIndex()
        assertThatThrownBy { index.get(LabelPrinter::class) }
            .isInstanceOf(NoSuchElementException::class.java)
            .hasMessage("no card for LabelPrinter")
        assertThatThrownBy { Callers.scale(index) }
            .isInstanceOf(NoSuchElementException::class.java)
            .hasMessage("no card for Scale")
    }

    @Test
    fun `a KClass key cannot tell a shelf of apples from a shelf of lemons`() {
        // both have the class Shelf, so the second card replaces the first
        val index = CardIndex()
        index.register(Shelf::class, FixedShelf(listOf(gala)))
        index.register(Shelf::class, FixedShelf(listOf(Lemon("Eureka", 120))))
        assertThat(index.get(Shelf::class).all()).containsExactly(Lemon("Eureka", 120))
    }

    @Test
    fun `KType keys keep a shelf of apples and a shelf of lemons apart`() {
        val index = CardIndex()
        val apples = FixedShelf(listOf(gala, Apple("Fuji", 150)))
        val lemons = FixedShelf(listOf(Lemon("Eureka", 120)))
        Callers.fileShelves(index, apples, lemons)

        assertThat(Callers.apples(index).all()).containsExactly(gala, Apple("Fuji", 150))
        assertThat(Callers.lemons(index).all()).containsExactly(Lemon("Eureka", 120))
    }

    @Test
    fun `getTyped by KType uses the full type, arguments included`() {
        val index = CardIndex()
        val lemons = FixedShelf(listOf(Lemon("Eureka", 120)))
        index.registerTyped(typeOf<Shelf<Lemon>>(), lemons)
        assertThat(index.getTyped(typeOf<Shelf<Lemon>>())).isSameAs(lemons)
        assertThatThrownBy { index.getTyped(typeOf<Shelf<Apple>>()) }
            .isInstanceOf(NoSuchElementException::class.java)
            .hasMessageStartingWith("no card for ")
    }
}
