package workbench.injector.app.l02

// Uses the component KSP wrote: build/generated/ksp/l02/kotlin/workbench/injector/app/l02/GeneratedMovingDayComponent.kt
//   ./gradlew :injector:app:demo -Pmain=workbench.injector.app.l02.MovingDayAppKt
fun main() {
    val plan: MovingDayComponent = GeneratedMovingDayComponent()
    plan.movingDay().plan().forEach(::println)
    println("one truck for the whole day: ${plan.truck() === plan.movingDay().crew.truck}")
}
