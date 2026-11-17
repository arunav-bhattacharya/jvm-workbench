package workbench.functional.l06

// Four functions from the app's meal planner. Each one compiles, reads fine at a glance, and has a bug
// caused by a scope function. The tests describe what each should do. Rewrite each function so it
// says what it means: often with fewer scope functions, sometimes with none.

/**
 * Adds [open] to the week's menu if a dish is open in the app. When none is open (open == null), asks the
 * recipe site for a suggestion with [suggest] and adds that. Returns Added with the slot id, or
 * AlreadyOnMenu when the menu says the dish is on it already.
 *
 * [suggest] downloads a recipe: call it only when no dish is open, and add at most once.
 */
fun planDish(open: Dish?, menu: WeekMenu, suggest: () -> Dish): PlanResult =
    open?.let { dish -> menu.add(dish)?.let { PlanResult.Added(it) } }
        ?: run {
            val dish = suggest()
            menu.add(dish)?.let { PlanResult.Added(it) } ?: PlanResult.AlreadyOnMenu(dish.id)
        }

/** Returns [dish] marked COOKING if it is PLANNED. A dish in any other stage comes back unchanged. */
fun startCooking(dish: Dish): Dish =
    dish.takeIf { it.stage == Stage.PLANNED }
        ?.also { it.copy(stage = Stage.COOKING) }
        ?: dish

/** Builds the oven program for [bake]: temperature and minutes from the recipe, the recipe's name on the oven's screen, and a long beep. */
fun ovenProgram(bake: Bake): OvenProgram =
    OvenProgram().apply {
        temperatureC = bake.temperatureC
        minutes = bake.minutes
        timer.apply {
            beep = "long"
            name = bake.recipe
        }
    }

/** "Lemon drizzle: 23 cm tin" for a cake whose tin exists, or "k-7: no tin" when the cake or its tin is missing. */
fun tinLabel(cakeId: String, cakes: Map<String, Cake>, tins: Map<String, Tin>): String =
    cakes[cakeId]?.let {
        tins[it.tinId]?.let { "${it.name}: ${it.sizeCm} cm tin" }
    } ?: "$cakeId: no tin"
