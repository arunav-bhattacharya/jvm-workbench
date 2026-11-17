package workbench.patterns.l04;

/**
 * Adapter: makes {@link OldWarehouseSystem} look like our {@link Warehouse} port.
 *
 * <p>Translate on the way in: our product name becomes the warehouse's item number
 * ({@link Units#itemNumber}) and grams become kilograms as a decimal string ({@link Units#toKilos}).
 *
 * <p>Translate on the way out: answer "00|holdId" is {@code Reserved(holdId)}; "51" is
 * {@code Refused("out of stock")}; "05" is {@code Refused("discontinued")}; any other code
 * {@code xx} is {@code Refused("warehouse code xx")}. A {@link WarehouseException} becomes
 * {@code Unavailable(message of the exception)}. Nothing from the old program (its exception, its
 * answer string) may leak past this class.
 */
public final class WarehouseAdapter implements Warehouse {
    private final OldWarehouseSystem old;

    public WarehouseAdapter(OldWarehouseSystem old) {
        this.old = old;
    }

    @Override
    public StockResult reserve(String product, long grams) {
        throw new UnsupportedOperationException("TODO: convert the arguments, call old.hold, map the answer and errors");
    }
}
