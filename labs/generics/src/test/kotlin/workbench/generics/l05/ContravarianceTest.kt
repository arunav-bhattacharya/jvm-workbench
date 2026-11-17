package workbench.generics.l05

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.generics.JavaSignatures

class ContravarianceTest {
    private val gala = Apple("Gala", 180)
    private val fuji = Apple("Fuji", 150)
    private val eureka = Lemon("Eureka", 120)

    @Test
    fun `CollectingBin remembers every item in order`() {
        val bin = CollectingBin<Fruit>()
        bin.drop(gala)
        bin.drop(eureka)
        assertThat(bin.items).containsExactly(gala, eureka)
    }

    @Test
    fun `CollectingBin items cannot be used to change what it remembers`() {
        val bin = CollectingBin<String>()
        bin.drop("Gala")
        val seen = bin.items
        bin.drop("Fuji")
        assertThat(seen).containsExactly("Gala")               // a snapshot, not a live view
        assertThat(bin.items).containsExactly("Gala", "Fuji")
    }

    @Test
    fun `dropAll drops every fruit and counts them`() {
        val bin = CollectingBin<Fruit>()
        assertThat(dropAll(listOf(gala, eureka, fuji), bin)).isEqualTo(3)
        assertThat(bin.items).containsExactly(gala, eureka, fuji)
    }

    @Test
    fun `Bin is declared in, so Java sees dropAll taking Bin of super Fruit`() {
        // Kotlin writes a ? super wildcard into a parameter only when the class is declared `in`
        assertThat(JavaSignatures.paramText("workbench.generics.l05.BinKt", "dropAll", 1))
            .`as`("dropAll's bin parameter as Java sees it (add `in` to Bin's type parameter)")
            .isEqualTo("Bin<? super Fruit>")
    }

    @Test
    fun `highest ranks a list of Apple with a Comparator of Fruit`() {
        val top: Apple = highest(listOf(fuji, gala), byWeight)
        assertThat(top).isEqualTo(gala)                         // 180 g beats 150 g
        assertThat(highest(listOf(1, 9, 4), naturalOrder<Int>())).isEqualTo(9)
    }

    @Test
    fun `highest of an empty list throws IllegalArgumentException`() {
        assertThatThrownBy { highest(emptyList<Apple>(), byWeight) }
            .isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `a listener for any Fruit can listen to a DeliveryBell of Apple`() {
        val log = mutableListOf<String>()
        val stockCount: (Fruit) -> Unit = { log += "stock ${it.name}" }
        val appleSign: (Apple) -> Unit = { log += "sign ${it.name} ${it.grams} g" }

        val bell = DeliveryBell<Apple>()
        bell.listen(stockCount)                     // compiles: Function1 is in in its parameter
        bell.listen(appleSign)

        assertThat(bell.ring(gala)).isEqualTo(2)
        assertThat(log).containsExactly("stock Gala", "sign Gala 180 g")
    }

    @Test
    fun `ring with no listeners calls nobody`() {
        assertThat(DeliveryBell<Lemon>().ring(eureka)).isZero()
    }
}
