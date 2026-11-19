package workbench.injector.l02.demo

// Three plans with a mistake each, worked out on the street by reflection: nothing complains until you ask.
//   ./gradlew :injector:demo -Pmain=workbench.injector.l02.demo.RunTimeMistakesDemoKt
fun main() {
    tryOnTheDay("missing: Driver has no @Inject") {
        ReflectionContainer().get(workbench.injector.l02.demo.missing.MovingDay::class.java)
    }
    tryOnTheDay("cycle: the driver waits for the truck") {
        ReflectionContainer().get(workbench.injector.l02.demo.cycle.MovingDay::class.java)
    }
    tryOnTheDay("twice: two routes, no names") {
        val day = ReflectionContainer(workbench.injector.l02.demo.twice.RouteModule)
            .get(workbench.injector.l02.demo.twice.MovingDay::class.java)
        "the driver takes the ${day.crew.truck.driver.route.name}"
    }
}

private fun tryOnTheDay(title: String, morning: () -> Any) {
    println("--- $title")
    try {
        println("no error: ${morning()}")
    } catch (e: Throwable) {
        println(e)
        println("  ${e.stackTrace.size} stack frames, the first three:")
        e.stackTrace.take(3).forEach { println("    at $it") }
    }
}
