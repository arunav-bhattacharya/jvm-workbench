package workbench.injector.app.l02

import workbench.injector.annotations.Component

@Component
interface MovingDayComponent {
    fun movingDay(): MovingDay
    fun truck(): Truck
}
