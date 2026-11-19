package workbench.injector.app.l03

/**
 * One cold start, run by StartupRace in a fresh JVM: wire the crew one way (args[0] is "generated" or
 * "reflection"), ask for the moving day twice, and print how long each step took, in microseconds.
 */
fun main(args: Array<String>) {
    val way = args.firstOrNull() ?: "generated"
    val t0 = System.nanoTime()
    val day: MovingDay
    val t1: Long
    val t2: Long
    if (way == "generated") {
        val plan = GeneratedMovingDayComponent()
        t1 = System.nanoTime()
        day = plan.movingDay()
        t2 = System.nanoTime()
        plan.movingDay()
    } else {
        val container = ReflectionContainer(RouteModule)
        t1 = System.nanoTime()
        day = container.get(MovingDay::class.java)
        t2 = System.nanoTime()
        container.get(MovingDay::class.java)
    }
    val t3 = System.nanoTime()
    println("probe $way create=${(t1 - t0) / 1000} first=${(t2 - t1) / 1000} second=${(t3 - t2) / 1000} ${day.plan().first()}")
}
