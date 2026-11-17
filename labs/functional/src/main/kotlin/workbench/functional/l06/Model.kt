package workbench.functional.l06

// The types the meal planner works with. You don't need to change this file.

enum class Stage { PLANNED, COOKING, SERVED, SKIPPED }

/** One dish for the week. */
data class Dish(val id: String, val name: String, val servings: Int, val stage: Stage)

/** This week's menu. add returns the new slot id, or null when a dish with this id is on the menu already. */
fun interface WeekMenu {
    fun add(dish: Dish): String?
}

sealed interface PlanResult {
    data class Added(val slotId: String) : PlanResult
    data class AlreadyOnMenu(val dishId: String) : PlanResult
}

/** A program for the oven. [name] is what the oven's screen shows while it bakes. */
class OvenProgram {
    var temperatureC: Int = 0
    var minutes: Int = 0
    var name: String = ""
    val timer = Timer()
}

class Timer {
    var beep: String = ""
    var name: String = ""   // a reminder the timer shows when it beeps, such as "turn the tray"; empty unless set
}

/** What a recipe says about baking it. */
data class Bake(val recipe: String, val temperatureC: Int, val minutes: Int)

data class Cake(val id: String, val name: String, val tinId: String)

data class Tin(val id: String, val name: String, val sizeCm: Int)
