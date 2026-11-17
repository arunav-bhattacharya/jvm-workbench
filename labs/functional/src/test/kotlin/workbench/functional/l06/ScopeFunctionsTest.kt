package workbench.functional.l06

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class ScopeFunctionsTest {

    private val soup = Dish("d-311", "Pumpkin soup", 4, Stage.PLANNED)

    /** A menu that remembers what is on it and counts every call. */
    private class FakeMenu(alreadyOnMenu: Set<String> = emptySet()) : WeekMenu {
        private val onMenu = alreadyOnMenu.toMutableSet()
        var calls = 0
        override fun add(dish: Dish): String? {
            calls++
            return if (onMenu.add(dish.id)) "slot-${dish.id}" else null
        }
    }

    private class CountingSuggest(private val dish: Dish) : () -> Dish {
        var calls = 0
        override fun invoke(): Dish { calls++; return dish }
    }

    // ---- planDish ----

    @Test
    fun `planDish adds the open dish without downloading anything`() {
        val menu = FakeMenu()
        val suggest = CountingSuggest(soup)
        assertThat(planDish(soup, menu, suggest)).isEqualTo(PlanResult.Added("slot-d-311"))
        assertThat(suggest.calls).`as`("downloads").isZero()
    }

    @Test
    fun `planDish downloads a suggestion and adds it when no dish is open`() {
        val menu = FakeMenu()
        val suggest = CountingSuggest(soup)
        assertThat(planDish(null, menu, suggest)).isEqualTo(PlanResult.Added("slot-d-311"))
        assertThat(suggest.calls).isEqualTo(1)
    }

    @Test
    fun `planDish reports an open dish that is on the menu already, without downloading or adding again`() {
        val menu = FakeMenu(alreadyOnMenu = setOf("d-311"))
        val suggest = CountingSuggest(soup)
        assertThat(planDish(soup, menu, suggest)).isEqualTo(PlanResult.AlreadyOnMenu("d-311"))
        assertThat(suggest.calls).`as`("downloads when a dish was open").isZero()
        assertThat(menu.calls).`as`("calls to add").isEqualTo(1)
    }

    @Test
    fun `planDish reports a suggestion that is on the menu already`() {
        val menu = FakeMenu(alreadyOnMenu = setOf("d-311"))
        assertThat(planDish(null, menu, CountingSuggest(soup))).isEqualTo(PlanResult.AlreadyOnMenu("d-311"))
        assertThat(menu.calls).isEqualTo(1)
    }

    // ---- startCooking ----

    @Test
    fun `startCooking marks a planned dish as cooking`() {
        assertThat(startCooking(soup)).isEqualTo(soup.copy(stage = Stage.COOKING))
    }

    @Test
    fun `startCooking leaves a served dish alone`() {
        val served = soup.copy(stage = Stage.SERVED)
        assertThat(startCooking(served)).isEqualTo(served)
    }

    // ---- ovenProgram ----

    @Test
    fun `ovenProgram puts the recipe's name on the oven's screen`() {
        val program = ovenProgram(Bake("Oat cookies", 180, 12))
        assertThat(program.name).`as`("the name on the oven's screen").isEqualTo("Oat cookies")
        assertThat(program.timer.name).`as`("the timer's reminder").isEmpty()
    }

    @Test
    fun `ovenProgram copies temperature and minutes and sets a long beep`() {
        val program = ovenProgram(Bake("Oat cookies", 180, 12))
        assertThat(program.temperatureC).isEqualTo(180)
        assertThat(program.minutes).isEqualTo(12)
        assertThat(program.timer.beep).isEqualTo("long")
    }

    // ---- tinLabel ----

    private val cakes = mapOf(
        "k-1" to Cake("k-1", "Lemon drizzle", "round-23"),
        "k-2" to Cake("k-2", "Carrot cake", "square-20"),
    )
    private val tins = mapOf("round-23" to Tin("round-23", "springform", 23))

    @Test
    fun `tinLabel names the cake and its tin size`() {
        assertThat(tinLabel("k-1", cakes, tins)).isEqualTo("Lemon drizzle: 23 cm tin")
    }

    @Test
    fun `tinLabel handles a missing cake and a missing tin`() {
        assertThat(tinLabel("k-7", cakes, tins)).isEqualTo("k-7: no tin")
        assertThat(tinLabel("k-2", cakes, tins)).isEqualTo("k-2: no tin")
    }
}
