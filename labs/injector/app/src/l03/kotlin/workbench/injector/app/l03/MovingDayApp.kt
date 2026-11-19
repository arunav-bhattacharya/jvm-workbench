package workbench.injector.app.l03

// The GPS stays off until the truck first asks for directions.
//   ./gradlew :injector:app:demo -Pmain=workbench.injector.app.l03.MovingDayAppKt
fun main() {
    val start = System.nanoTime()
    fun ms() = (System.nanoTime() - start) / 1_000_000
    val plan: MovingDayComponent = GeneratedMovingDayComponent()
    val day = plan.movingDay()
    println("crew ready after ${ms()} ms, GPS switched on: ${GpsUnit.switchedOn}")
    day.plan().forEach(::println)
    println(plan.truck().directions())
    println("first directions after ${ms()} ms, GPS switched on: ${GpsUnit.switchedOn}")
    println(plan.truck().directions())
    println("second directions after ${ms()} ms, GPS switched on: ${GpsUnit.switchedOn}")
}
