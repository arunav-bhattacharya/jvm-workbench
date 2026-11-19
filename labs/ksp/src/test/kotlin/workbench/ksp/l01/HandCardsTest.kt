package workbench.ksp.l01

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

// The four sample objects and their cards, shared by this lesson's tests.
internal val box = Box("kitchen 1", "kitchen", 5200, fragile = true)
internal val lamp = Lamp("desk lamp", 1, null)
internal val bookshelf = Bookshelf(3, listOf("atlas", "cookbook"))
internal val plant = Plant("fern", 2.5)

internal const val BOX_CARD = "Box: label=kitchen 1, room=kitchen, weightGrams=5200, fragile=true"
internal const val LAMP_CARD = "Lamp: name=desk lamp, bulbs=1, shade=null"
internal const val BOOKSHELF_CARD = "Bookshelf: shelves=3, books=[atlas, cookbook]"
internal const val PLANT_CARD = "Plant: kind=fern, potLitres=2.5, waterEveryDays=7"

class HandCardsTest {

    @Test
    fun `Box's card is given, as the example of the format`() {
        assertThat(box.inventoryCard()).isEqualTo(BOX_CARD)
    }

    @Test
    fun `Bookshelf's card is given too, and a list prints in brackets`() {
        assertThat(bookshelf.inventoryCard()).isEqualTo(BOOKSHELF_CARD)
    }

    @Test
    fun `Lamp's card, written by hand, prints a missing shade as null`() {
        assertThat(lamp.inventoryCard()).isEqualTo(LAMP_CARD)
    }

    @Test
    fun `Plant's card, written by hand, includes the default it was built with`() {
        assertThat(plant.inventoryCard()).isEqualTo(PLANT_CARD)
    }
}
