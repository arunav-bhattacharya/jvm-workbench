package workbench.injector.app.l03

import workbench.injector.annotations.Component

@Component
interface MovingDayComponent {
    fun movingDay(): MovingDay
    fun truck(): Truck
}
