package workbench.functional.l06

fun planDish(open: Dish?, menu: WeekMenu, suggest: () -> Dish): PlanResult {
    val dish = open ?: suggest()                       // download only when no dish is really open
    val slotId = menu.add(dish)                        // add exactly once
        ?: return PlanResult.AlreadyOnMenu(dish.id)
    return PlanResult.Added(slotId)
}
// The bug: in `open?.let { A } ?: run { B }`, B runs whenever A's *result* is null, and menu.add
// returns null for a dish that is on the menu already. So an open dish that was planned before
// made the planner download a suggestion and add that as well.

fun startCooking(dish: Dish): Dish =
    if (dish.stage == Stage.PLANNED) dish.copy(stage = Stage.COOKING)   // return the copy
    else dish
// The bug: also { } takes a (T) -> Unit block, so the copy it made was thrown away, and also returned the original.

fun ovenProgram(bake: Bake): OvenProgram =
    OvenProgram().apply {
        temperatureC = bake.temperatureC
        minutes = bake.minutes
        name = bake.recipe                             // set on the program: no inner receiver in the way
        timer.beep = "long"                            // one property needs no nested apply
    }
// The bug: inside timer.apply { }, an unqualified `name` means timer.name, the innermost receiver.

fun tinLabel(cakeId: String, cakes: Map<String, Cake>, tins: Map<String, Tin>): String {
    val cake = cakes[cakeId] ?: return "$cakeId: no tin"
    val tin = tins[cake.tinId] ?: return "$cakeId: no tin"
    return "${cake.name}: ${tin.sizeCm} cm tin"        // two names, no guessing which `it`
}
// The bug: the inner `it` (the tin) hid the outer `it` (the cake), so it.name was the tin's name.
