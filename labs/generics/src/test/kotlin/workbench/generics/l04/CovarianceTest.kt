package workbench.generics.l04

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.generics.JavaSignatures

class CovarianceTest {
    private val gala = Apple("Gala", 180)
    private val fuji = Apple("Fuji", 150)
    private val lemon = Lemon("Eureka", 120)

    @Test
    fun `Dispenser hands out items in order and remembers the last one`() {
        val dispenser = Dispenser(listOf<Fruit>(gala, fuji))
        assertThat(dispenser.lastServed).isNull()
        assertThat(dispenser.hasNext()).isTrue()
        assertThat(dispenser.next()).isEqualTo(gala)
        assertThat(dispenser.lastServed).isEqualTo(gala)
        assertThat(dispenser.next()).isEqualTo(fuji)
        assertThat(dispenser.lastServed).isEqualTo(fuji)
        assertThat(dispenser.hasNext()).isFalse()
    }

    @Test
    fun `next on an empty dispenser throws NoSuchElementException`() {
        val dispenser = Dispenser(emptyList<Fruit>())
        assertThatThrownBy { dispenser.next() }.isInstanceOf(NoSuchElementException::class.java)
    }

    @Test
    fun `nextOr gives the next item, then the fallback`() {
        val dispenser = Dispenser(listOf("Gala"))
        assertThat(dispenser.nextOr("none")).isEqualTo("Gala")
        assertThat(dispenser.nextOr("none")).isEqualTo("none")
    }

    @Test
    fun `drainAll and totalGrams empty the dispenser`() {
        assertThat(drainAll(Dispenser(listOf<Fruit>(gala, lemon)))).containsExactly(gala, lemon)
        val dispenser = Dispenser(listOf<Fruit>(gala, fuji, lemon))
        assertThat(totalGrams(dispenser)).isEqualTo(450)
        assertThat(dispenser.hasNext()).isFalse()
    }

    @Test
    fun `Dispenser is declared out, so Java sees drainAll taking Dispenser of extends Fruit`() {
        // Kotlin writes a ? extends wildcard into a parameter only when the class is declared `out`
        assertThat(JavaSignatures.paramText("workbench.generics.l04.DispenserKt", "drainAll"))
            .`as`("drainAll's parameter as Java sees it (add `out` to Dispenser's type parameter)")
            .isEqualTo("Dispenser<? extends Fruit>")
    }

    @Test
    fun `callers cannot set lastServed`() {
        val publicSetters = Dispenser::class.java.methods.filter { it.name == "setLastServed" }
        assertThat(publicSetters).isEmpty()
    }

    @Test
    fun `Tray map transforms every item and keeps the label`() {
        val tray = Tray(listOf(gala, fuji), label = "window display")
        val names: Tray<String> = tray.map { it.name }
        assertThat(names).isEqualTo(Tray(listOf("Gala", "Fuji"), "window display"))
    }

    @Test
    fun `firstOnTray returns the first piece of fruit or null`() {
        assertThat(firstOnTray(Tray(listOf<Fruit>(lemon, gala), null))).isEqualTo(lemon)
        assertThat(firstOnTray(Tray(emptyList(), null))).isNull()
    }

    @Test
    fun `Tray is declared out, so Java sees firstOnTray taking Tray of extends Fruit`() {
        assertThat(JavaSignatures.paramText("workbench.generics.l04.TrayKt", "firstOnTray"))
            .`as`("firstOnTray's parameter as Java sees it (add `out` to Tray's type parameter)")
            .isEqualTo("Tray<? extends Fruit>")
    }
}
