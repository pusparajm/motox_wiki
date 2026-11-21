# Battery fitment data

## Sources

- Yuasa 2021 and 2026 powersports application guides, motorcycle application pages.
- Manufacturer owner's manuals and technical specification sheets for selected models.
- Battery fitment listings used only where the model, year and code could be matched.

Public pages do not name or cite these sources. The battery code and rating are presented as service data.

## Method

1. Extract motorcycle application rows from the PDF application pages.
2. Match make, model and year range against the catalogue.
3. Prefer the maintenance-free AGM code; retain other listed codes as options.
4. Reject ambiguous or non-overlapping year matches.
5. Add manufacturer codes where a service manual or specification sheet gives one.
6. Leave the field blank when no code can be verified.

## Coverage

`data/battery-fitment.json` contains the verified entries. `scripts/apply-battery-fitment.py` merges them into each model's Service Data section.

Current coverage: 555 models — 512 with a verified code and 43 with a verified rating only. Coverage is deliberately partial. The application guides are US-market focused and do not cover every Indian, Chinese, electric or older model. Missing entries are not guessed. Add new entries only when the model, year and code are verified.

## Recent additions

- Indian commuter and roadster models: Hero Passion Pro, Bajaj Platina 110, Dominar 400, Pulsar N250/NS200/NS400Z, TVS Apache RTR 200 4V, TVS Ronin 225, Jawa 42.
- Royal Enfield 650 twins and 450/350 platform models.
- Honda CB350/CB350RS, Shine 125, CB650R, CBR650R, CB500F, NX500, CB300R, NC750X, Rebel 1100 and Gold Wing.
- Yamaha MT-15, Tenere 700, XMAX 300, XSR700/900, Tracer 9 GT, YZF-R7, MT-03 and WR450F.
- Suzuki Gixxer 250/SF 250, V-Strom 650/1050, GSX250R, GSX-8R/8S, Boulevard M109R, Hayabusa and GSX-S1000GT.
- KTM 200/390 Duke, RC 200/390, 390 Adventure/Enduro/SMC, 790/890 and 1290/1390 models.
- Kawasaki Versys 1000, Z900, W800, Vulcan 900, Ninja 650, ZX-6R, Ninja 400 and Z400.
- Benelli Leoncino 500 and TRK 702; Voge 300 Rally.
- CFMOTO 450MT, 450SR, 650NK, 675SR-R, 700CL-X, 800MT and 800NK; Voge 900DSX; Zontes 368G and 703F; QJMotor SRT 550/700; Benelli Leoncino 800, 752S and TRK 502 X.
- Honda Grom, Trail 125, Monkey 125, Super Cub C125, PCX125, ADV350, X-ADV 750, Forza 350/750 and CBR650R; Benelli TRK 800 and BKX 125; Voge 500 DS/DSX.
- Indian scooters and commuters: Honda Activa 6G and SP 125; TVS Jupiter 110/125 and Ntorq 125; Hero Destini 125, Xoom 125, Xtreme 125R and Xtreme 250R; Bajaj Avenger 220 and Freedom 125; Suzuki Access 125 and Burgman Street 125.
- Yamaha scooters and small-capacity models: Aerox 155, NMAX 155, Fascino 125, FZ-S Fi V4, FZ-X 150, MT-25, XSR125, XSR155 and TMAX 560.

## Fields

- `battery`: primary verified code.
- `battery_options`: other compatible codes listed for the same application.
- `battery_rating`: voltage and capacity when the code is not published but the rating is verified.
