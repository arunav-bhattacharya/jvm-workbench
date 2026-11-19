package workbench.injector.app.l01

import workbench.injector.annotations.Component

/** What the app asks the plan for. KSP writes GeneratedMovingDayComponent, which implements it. */
@Component
interface MovingDayComponent {
    fun movingDay(): MovingDay
    fun truck(): Truck
}
