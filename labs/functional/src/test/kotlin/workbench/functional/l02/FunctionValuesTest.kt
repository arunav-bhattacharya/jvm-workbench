package workbench.functional.l02

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.util.concurrent.CountDownLatch
import kotlin.concurrent.thread

class FunctionValuesTest {
    private val soup = Dish("pumpkin soup", 40, "vegan", "pumpkin")

    @Test
    fun `readyWithin rejects slower dishes and lets the limit itself through`() {
        val check = readyWithin(60)
        assertThat(check(soup.copy(minutes = 60))).isNull()
        assertThat(check(soup.copy(name = "stew", minutes = 61))).isEqualTo(Problem("too-slow", "stew"))
    }

    @Test
    fun `two time checks keep their own limits`() {
        val quick = readyWithin(20)
        val relaxed = readyWithin(240)
        assertThat(quick(soup)).isEqualTo(Problem("too-slow", "pumpkin soup"))
        assertThat(relaxed(soup)).isNull()
    }

    @Test
    fun `meatFree rejects dishes whose diet has meat`() {
        assertThat(meatFree(soup)).isNull()
        assertThat(meatFree(soup.copy(diet = "vegetarian"))).isNull()
        assertThat(meatFree(soup.copy(diet = "meat"))).isEqualTo(Problem("has-meat", "pumpkin soup"))
    }

    @Test
    fun `seasonCheck and inSeason agree`() {
        val strawberry = soup.copy(main = "strawberry")
        assertThat(inSeason(soup)).isNull()
        assertThat(inSeason(strawberry)).isEqualTo(Problem("out-of-season", "pumpkin soup"))
        assertThat(seasonCheck(soup)).isNull()
        assertThat(seasonCheck(strawberry)).isEqualTo(Problem("out-of-season", "pumpkin soup"))
    }

    @Test
    fun `firstProblem returns the first problem in check order, or null`() {
        val checks = listOf(readyWithin(60), meatFree, seasonCheck)
        assertThat(firstProblem(soup, checks)).isNull()
        val bad = soup.copy(minutes = 90, diet = "meat")
        assertThat(firstProblem(bad, checks)).isEqualTo(Problem("too-slow", "pumpkin soup"))
        assertThat(firstProblem(bad, checks.reversed())).isEqualTo(Problem("has-meat", "pumpkin soup"))
    }

    @Test
    fun `firstProblem stops at the first problem`() {
        var guestCalls = 0
        val askTheGuest: Check = { guestCalls++; null }
        firstProblem(soup.copy(diet = "meat"), listOf(meatFree, askTheGuest))
        assertThat(guestCalls).`as`("checks after the first problem must not run").isZero()
        firstProblem(soup, listOf(meatFree, askTheGuest))
        assertThat(guestCalls).isEqualTo(1)
    }

    @Test
    fun `allProblems collects every problem in check order`() {
        val checks = listOf(readyWithin(60), meatFree, seasonCheck)
        val bad = Dish("beef roast", 150, "meat", "beef")
        assertThat(allProblems(bad, checks).map { it.check })
            .containsExactly("too-slow", "has-meat", "out-of-season")
        assertThat(allProblems(soup, checks)).isEmpty()
    }

    @Test
    fun `suits calls the optional callback only when there is a problem`() {
        val checks = listOf(meatFree)
        assertThat(suits(soup, checks)).isTrue()
        assertThat(suits(soup.copy(diet = "meat"), checks)).`as`("no callback given: must not fail").isFalse()

        val seen = mutableListOf<Problem>()
        assertThat(suits(soup, checks) { seen += it }).isTrue()
        assertThat(suits(soup.copy(diet = "meat"), checks) { seen += it }).isFalse()
        assertThat(seen).containsExactly(Problem("has-meat", "pumpkin soup"))
    }

    @Test
    fun `makeCounter counts 1, 2, 3 and two counters are independent`() {
        val a = makeCounter()
        val b = makeCounter()
        assertThat(listOf(a(), a(), a())).containsExactly(1, 2, 3)
        assertThat(b()).isEqualTo(1)
        assertThat(a()).isEqualTo(4)
    }

    @Test
    fun `a shared counter loses no updates on 8 threads`() {
        val threads = 8
        val perThread = 200_000
        // Several rounds: one lucky round proves nothing, a broken counter loses updates in at least one.
        repeat(5) { round ->
            val counter = makeSharedCounter()
            val ready = CountDownLatch(threads)
            val go = CountDownLatch(1)
            val workers = List(threads) {
                thread {
                    ready.countDown()
                    go.await()
                    repeat(perThread) { counter() }
                }
            }
            ready.await()
            go.countDown()
            workers.forEach { it.join() }
            val expectedNext = threads.toLong() * perThread + 1
            assertThat(counter()).`as`("round ${round + 1}: the next value after ${threads * perThread} calls").isEqualTo(expectedNext)
        }
    }
}
