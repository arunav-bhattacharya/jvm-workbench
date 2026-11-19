package workbench.injector.app.l03

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Singleton

@Singleton
class Crew @Inject constructor(val truck: Truck, val kitchenPacker: Packer, val bedroomPacker: Packer)
