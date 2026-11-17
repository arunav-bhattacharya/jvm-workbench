package workbench.flows.l05

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.asFlow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

@OptIn(ExperimentalCoroutinesApi::class) // currentTime is experimental in kotlinx-coroutines-test 1.11.0
class FlatteningTest {

    /** A fake stove on virtual time. It counts how many dishes are on the burners at once. */
    private class FakeStove(private val cookingMs: (String) -> Long, private val burns: Set<String> = emptySet()) : Stove {
        var onBurners = 0
        var mostOnBurners = 0
        var calls = 0
        override suspend fun cook(dish: String): Plate {
            calls++
            onBurners++
            mostOnBurners = maxOf(mostOnBurners, onBurners)
            try {
                delay(cookingMs(dish))
                if (dish in burns) throw Burnt(dish)
                return Plate(dish)
            } finally {
                onBurners--
            }
        }
    }

    /** Collects a flow and records the virtual time at which each value arrived. */
    private suspend fun <T> TestScope.timed(flow: Flow<T>): List<Pair<Long, T>> {
        val seen = mutableListOf<Pair<Long, T>>()
        flow.collect { seen += currentTime to it }
        return seen
    }

    // ---- cookAll: a capped fan-out ----

    @Test
    fun `cookAll cooks 4 dishes at once, so 10 dishes of 100 ms take 300 ms`() = runTest {
        val stove = FakeStove({ 100 })
        val dishes = (1..10).map { "dish-$it" }
        val plates = cookAll(dishes.asFlow(), stove).toList()
        assertThat(plates.map { it.dish }).containsExactlyInAnyOrderElementsOf(dishes)
        assertThat(stove.mostOnBurners).`as`("dishes on the burners at the busiest moment").isEqualTo(4)
        assertThat(currentTime).`as`("virtual ms: three rounds of 4, 4 and 2").isEqualTo(300)
    }

    @Test
    fun `cookAll never uses more than 4 burners, even for 40 dishes`() = runTest {
        val stove = FakeStove({ 100 })
        val plates = cookAll((1..40).map { "dish-$it" }.asFlow(), stove).toList()
        assertThat(plates).hasSize(40)
        assertThat(stove.mostOnBurners).isEqualTo(4)
        assertThat(currentTime).isEqualTo(1000)
    }

    @Test
    fun `cookAll passes plates on in the order they are ready`() = runTest {
        val cooking = mapOf("soup" to 300L, "salad" to 100L, "roast" to 200L)
        val seen = timed(cookAll(cooking.keys.asFlow(), FakeStove({ cooking.getValue(it) })))
        assertThat(seen.map { it.second.dish to it.first })
            .containsExactly("salad" to 100L, "roast" to 200L, "soup" to 300L)
    }

    // ---- cookAllOrSubstitute: one burnt dish must not take the others down ----

    private val substitute = { dish: String -> Plate(dish, "substitute") }

    @Test
    fun `cookAllOrSubstitute gives a burnt dish its substitute and keeps the others`() = runTest {
        val cooking = mapOf("soup" to 300L, "salad" to 100L, "roast" to 200L)
        val stove = FakeStove({ cooking.getValue(it) }, burns = setOf("salad"))
        val seen = timed(cookAllOrSubstitute(cooking.keys.asFlow(), stove, substitute))
        assertThat(seen.map { Triple(it.second.dish, it.second.madeBy, it.first) }).containsExactly(
            Triple("salad", "substitute", 100L),
            Triple("roast", "stove", 200L),
            Triple("soup", "stove", 300L),
        )
    }

    @Test
    fun `cookAllOrSubstitute still uses at most 4 burners`() = runTest {
        val stove = FakeStove({ 100 }, burns = setOf("dish-3", "dish-7"))
        val plates = cookAllOrSubstitute((1..10).map { "dish-$it" }.asFlow(), stove, substitute).toList()
        assertThat(plates.filter { it.madeBy == "substitute" }.map { it.dish }).containsExactlyInAnyOrder("dish-3", "dish-7")
        assertThat(stove.mostOnBurners).isEqualTo(4)
        assertThat(currentTime).isEqualTo(300)
    }

    @Test
    fun `cookAllOrSubstitute lets a failure that is not a burnt dish reach the caller`() = runTest {
        val stove = Stove { dish -> delay(50); if (dish == "roast") error("the gas went out") else Plate(dish) }
        val failure = runCatching { cookAllOrSubstitute(listOf("soup", "roast").asFlow(), stove, substitute).toList() }
            .exceptionOrNull()
        assertThat(failure).isInstanceOf(IllegalStateException::class.java).hasMessage("the gas went out")
    }

    // ---- ovenGaps: the latest of each ----

    /** Thermometer readings 150, 152, ... 160, one every 100 ms from t=100. */
    private fun readings(): Flow<Int> = flow { for (c in 150..160 step 2) { delay(100); emit(c) } }

    /** The dial: turned to 180 at t=250, then to 200 at t=550. */
    private fun dial(): Flow<Int> = flow { delay(250); emit(180); delay(300); emit(200) }

    @Test
    fun `ovenGaps waits for the dial, then uses the latest reading`() = runTest {
        val first = timed(ovenGaps(readings(), dial())).first()
        assertThat(first.first).`as`("virtual ms of the first line: when the dial was first set").isEqualTo(250)
        assertThat(first.second).isEqualTo(OvenGap(152, 180, 28))
    }

    @Test
    fun `ovenGaps shows one line per update of either flow`() = runTest {
        val seen = timed(ovenGaps(readings(), dial()))
        assertThat(seen.map { it.first to "${it.second.celsius}/${it.second.dial}" }).containsExactly(
            250L to "152/180",
            300L to "154/180",
            400L to "156/180",
            500L to "158/180",
            550L to "158/200",
            600L to "160/200",
        )
    }
}
