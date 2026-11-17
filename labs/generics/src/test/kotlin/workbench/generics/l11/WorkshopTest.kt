package workbench.generics.l11

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.generics.JavaSignatures

class WorkshopTest {

    // ---- Either ----

    private fun parseGrams(text: String): Either<String, Long> =
        text.toLongOrNull()?.let { Either.Right(it) } ?: Either.Left("not a number: $text")

    @Test
    fun `map transforms a Right and passes a Left through`() {
        assertThat(parseGrams("1250").map { it * 2 }).isEqualTo(Either.Right(2500L))
        val failed: Either<String, String> = parseGrams("x").map { "$it g" }
        assertThat(failed).isEqualTo(Either.Left("not a number: x"))
    }

    @Test
    fun `getOrElse returns the Right value or the fallback for a Left`() {
        assertThat(parseGrams("180").getOrElse { -1 }).isEqualTo(180L)
        assertThat(parseGrams("oops").getOrElse { it.length.toLong() }).isEqualTo(18L)   // "not a number: oops"
    }

    // ---- Storeroom ----

    @Test
    fun `InMemoryStoreroom saves, finds by id and lists in id order`() {
        val suppliers = InMemoryStoreroom<Supplier, Long>()
        suppliers.save(Supplier(7, "Orchard Lane"))
        suppliers.save(Supplier(2, "Hill Farm"))
        assertThat(suppliers.findById(7)).isEqualTo(Supplier(7, "Orchard Lane"))
        assertThat(suppliers.findById(99)).isNull()
        assertThat(suppliers.findAll().map { it.id }).containsExactly(2L, 7L)
    }

    @Test
    fun `saveAll saves every item and returns them in the order given`() {
        val crates = InMemoryStoreroom<Crate, String>()
        val saved = crates.saveAll(listOf(Crate("c-2", 9_000), Crate("c-1", 12_000)))
        assertThat(saved.map { it.id }).containsExactly("c-2", "c-1")
        assertThat(crates.findAll().map { it.id }).containsExactly("c-1", "c-2")
    }

    @Test
    fun `describeAll prints one line per item`() {
        val view = object : DisplayCase<Item<*>> {
            override fun findAll(): List<Item<*>> = listOf(Supplier(1, "Hill Farm"), Crate("c-9", 8_000))
        }
        assertThat(describeAll(view)).containsExactly("item 1", "item c-9")
    }

    @Test
    fun `DisplayCase is covariant, so describeAll accepts a storeroom of any item`() {
        // with `out T`, Kotlin writes a ? extends wildcard into describeAll's Java signature
        assertThat(JavaSignatures.paramText("workbench.generics.l11.StoreroomKt", "describeAll", 0))
            .`as`("describeAll's parameter as Java sees it (add `out` to DisplayCase)")
            .isEqualTo("DisplayCase<? extends Item<?>>")
    }

    // ---- BellBoard ----

    @Test
    fun `ring calls the listeners for the item's class, in order, and counts them`() {
        val board = BellBoard()
        val log = mutableListOf<String>()
        board.listen(Apple::class) { log += "sign ${it.name}" }
        board.listen(Apple::class) { log += "scale ${it.grams}" }
        board.listen(Lemon::class) { log += "lemon ${it.name}" }

        assertThat(board.ring(Apple("Gala", 180))).isEqualTo(2)
        assertThat(log).containsExactly("sign Gala", "scale 180")
    }

    @Test
    fun `a listener for every Fruit can listen to one kind`() {
        val board = BellBoard()
        val log = mutableListOf<String>()
        val stockCount: (Fruit) -> Unit = { log += "stock ${it.name}" }
        board.listen(Apple::class, stockCount)    // (Fruit) -> Unit is an (Apple) -> Unit
        board.listen(Lemon::class, stockCount)
        board.ring(Apple("Gala", 180))
        board.ring(Lemon("Eureka", 120))
        assertThat(log).containsExactly("stock Gala", "stock Eureka")
    }

    @Test
    fun `reified listen takes the class from the type argument`() {
        val board = BellBoard()
        val log = mutableListOf<String>()
        Callers.onApple(board) { log += "apple ${it.grams}" }
        Callers.onLemon(board) { log += "lemon ${it.grams}" }
        board.ring(Lemon("Eureka", 120))
        assertThat(log).containsExactly("lemon 120")
    }

    @Test
    fun `ring with no listeners for that class calls nobody`() {
        val board = BellBoard()
        val log = mutableListOf<String>()
        board.listen(Apple::class) { log += "apple" }
        assertThat(board.ring(Lemon("Eureka", 120))).isZero()
        assertThat(log).isEmpty()
    }

    // ---- Attributes ----

    @Test
    fun `attributes return the value with the key's type, or null`() {
        val attrs = Attributes()
        attrs[Callers.varieties()] = listOf("Gala", "Fuji")
        val varieties: List<String>? = attrs[Callers.varieties()]   // no cast at the call site
        assertThat(varieties).containsExactly("Gala", "Fuji")
        assertThat(attrs[Callers.totalWeight()]).isNull()
        assertThat(attrs.getOrDefault(Callers.totalWeight(), 0)).isEqualTo(0)
    }

    @Test
    fun `keys with the same name but different types do not collide`() {
        val attrs = Attributes()
        attrs[Callers.weighings()] = listOf(180, 150)
        attrs[Callers.totalWeight()] = 330
        assertThat(Callers.weighings()).isNotEqualTo(Callers.totalWeight())   // same name, different KType
        assertThat(attrs[Callers.weighings()]).containsExactly(180, 150)
        assertThat(attrs[Callers.totalWeight()]).isEqualTo(330)
    }

    @Test
    fun `remove returns the old value and clears it`() {
        val attrs = Attributes()
        attrs[Callers.totalWeight()] = 330
        assertThat(attrs.remove(Callers.totalWeight())).isEqualTo(330)
        assertThat(attrs[Callers.totalWeight()]).isNull()
        assertThat(attrs.remove(Callers.totalWeight())).isNull()
    }
}
