package workbench.patterns.l04;

public final class WarehouseAdapter implements Warehouse {
    private final OldWarehouseSystem old;

    public WarehouseAdapter(OldWarehouseSystem old) {
        this.old = old;
    }

    @Override
    public StockResult reserve(String product, long grams) {
        String raw;
        try {
            // 1. translate our words into the old program's on the way in
            raw = old.hold(Units.itemNumber(product), Units.toKilos(grams));
        } catch (WarehouseException e) {
            // 2. the old program's checked exception stops here and becomes one of our results
            return new StockResult.Unavailable(e.getMessage());
        }
        // 3. translate the packed answer string into our sealed result on the way out
        String[] parts = raw.split("\\|", -1);
        String code = parts[0];
        return switch (code) {
            case "00" -> new StockResult.Reserved(parts.length > 1 ? parts[1] : "");
            case "51" -> new StockResult.Refused("out of stock");
            case "05" -> new StockResult.Refused("discontinued");
            default -> new StockResult.Refused("warehouse code " + code);
        };
    }
}
