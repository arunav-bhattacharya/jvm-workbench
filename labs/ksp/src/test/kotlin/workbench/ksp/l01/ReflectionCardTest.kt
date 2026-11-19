package workbench.ksp.l01

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.ksp.annotations.Inventory

/** A class nobody wrote a card for. */
@Inventory
class Rug(val colour: String, val metres: Double)

/** A class without the sticky note. */
class Wardrobe(val doors: Int)

class ReflectionCardTest {

    @Test
    fun `gives the same four cards as the hand-written ones`() {
        assertThat(reflectionCard(box)).isEqualTo(BOX_CARD)
        assertThat(reflectionCard(lamp)).isEqualTo(LAMP_CARD)
        assertThat(reflectionCard(bookshelf)).isEqualTo(BOOKSHELF_CARD)
        assertThat(reflectionCard(plant)).isEqualTo(PLANT_CARD)
    }

    @Test
    fun `needs no card written for a new class`() {
        assertThat(reflectionCard(Rug("red", 2.0))).isEqualTo("Rug: colour=red, metres=2.0")
    }

    @Test
    fun `refuses a class without @Inventory, but only when the program runs`() {
        assertThatThrownBy { reflectionCard(Wardrobe(2)) }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("Wardrobe has no @Inventory note")
    }
}
