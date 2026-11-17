package workbench.functional.l05

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class LazyPipelinesTest {

    // 200,000 recipes; every fourth one (ids 1, 5, 9, ...) is vegetarian
    private val book = List(200_000) { i ->
        Recipe(
            id = i + 1L,
            title = "recipe-${i + 1}",
            minutes = 10 + (i * 7) % 110,
            vegetarian = i % 4 == 0,
        )
    }

    // the matching service likes four recipes; 15,002 is not vegetarian
    private val liked = setOf(4_217L, 9_001L, 12_345L, 15_002L)

    private class CountingService(private val liked: Set<Long>) : (Recipe) -> Int {
        var calls = 0
        private val seen = mutableListOf<Recipe>()
        val nonVegetarianCalls get() = seen.count { !it.vegetarian }
        override fun invoke(r: Recipe): Int {
            calls++
            if (!r.vegetarian) seen += r
            return if (r.id in liked) 95 else (r.id % 89).toInt()
        }
    }

    @Test
    fun `firstMatch finds the first recipe the service likes`() {
        val service = CountingService(liked)
        assertThat(firstMatch(book, service)?.id).isEqualTo(4_217L)
    }

    @Test
    fun `firstMatch scores only up to the first match`() {
        val service = CountingService(liked)
        firstMatch(book, service)
        assertThat(service.calls).`as`("matching service calls for a match at position 4,217").isEqualTo(4_217)
    }

    @Test
    fun `firstMatch returns null and scores everything when nothing matches`() {
        val service = CountingService(emptySet())
        assertThat(firstMatch(book, service)).isNull()
        assertThat(service.calls).isEqualTo(200_000)
    }

    @Test
    fun `firstMatchesFor stops at the nth match and never scores a recipe that isn't vegetarian`() {
        val service = CountingService(liked)
        assertThat(firstMatchesFor(book, service, 2)).containsExactly(4_217L, 9_001L)
        assertThat(service.nonVegetarianCalls).`as`("non-vegetarian recipes sent to the service").isZero()
        // vegetarian ids are 1, 5, 9, ... so 9,001 is the 2,251st vegetarian recipe
        assertThat(service.calls).`as`("matching service calls").isEqualTo(2_251)
    }

    @Test
    fun `firstMatchesFor returns fewer ids when the book runs out`() {
        val service = CountingService(liked)
        assertThat(firstMatchesFor(book, service, 5)).containsExactly(4_217L, 9_001L, 12_345L)
        assertThat(service.calls).isEqualTo(50_000)
    }

    // ---- allResults: a paging sequence ----

    private class FakeSite(private val pages: List<List<Recipe>>) : RecipeSite {
        val fetched = mutableListOf<Int>()
        override fun page(number: Int): List<Recipe> {
            fetched += number
            return pages.getOrElse(number) { error("page $number does not exist: the app read past the empty page") }
        }
    }

    private fun recipe(id: Long, minutes: Int) = Recipe(id, "recipe-$id", minutes, vegetarian = true)

    private fun threePagesThenEmpty() = FakeSite(
        listOf(
            listOf(recipe(1, 45), recipe(2, 30), recipe(3, 60)),
            listOf(recipe(4, 10), recipe(5, 40), recipe(6, 25)),
            listOf(recipe(7, 35)),
            emptyList(),
        )
    )

    @Test
    fun `allResults fetches nothing until a terminal operation runs`() {
        val site = threePagesThenEmpty()
        val results = allResults(site).filter { it.minutes > 0 }.map { it.id }
        assertThat(site.fetched).`as`("pages fetched before anyone asked").isEmpty()
        assertThat(results.first()).isEqualTo(1L)
        assertThat(site.fetched).containsExactly(0)
    }

    @Test
    fun `allResults fetches only the pages it needs`() {
        val site = threePagesThenEmpty()
        assertThat(allResults(site).first { it.minutes <= 15 }.id).isEqualTo(4L)
        assertThat(site.fetched).containsExactly(0, 1)
    }

    @Test
    fun `allResults returns every recipe in order and stops at the empty page`() {
        val site = threePagesThenEmpty()
        assertThat(allResults(site).map { it.id }.toList()).containsExactly(1L, 2L, 3L, 4L, 5L, 6L, 7L)
        assertThat(site.fetched).containsExactly(0, 1, 2, 3)
    }

    @Test
    fun `allResults starts again from page 0 each time it is read`() {
        val site = threePagesThenEmpty()
        val results = allResults(site)
        assertThat(results.count()).isEqualTo(7)
        assertThat(results.count()).isEqualTo(7)
        assertThat(site.fetched).containsExactly(0, 1, 2, 3, 0, 1, 2, 3)
    }
}
