# CHANGELOG

<!-- version list -->

## v1.0.0-dev.28 (2026-10-17)

### Code Style

- Rename struct_
  ([`b994bd3`](https://github.com/lugovskovp/QGIS_VDO/commit/b994bd3b4e7e62429b9760cdaec026118cbe814a))

### Features

- Add list.__eq__, tests covered
  ([`7ed4feb`](https://github.com/lugovskovp/QGIS_VDO/commit/7ed4feb58e4e1b61583ec9e196eeab79f3092bf8))

- Add POI_ITEM, POI_BRIF, POI_DETAILS, POI
  ([`0abe548`](https://github.com/lugovskovp/QGIS_VDO/commit/0abe548617cc61a04878443b5fec44b30b3677ed))

- Block 0x10 - poi list
  ([`ecbc85e`](https://github.com/lugovskovp/QGIS_VDO/commit/ecbc85e17989cb26d6ce57c109a42750f06d5fb9))

- Сохранять и POI._zero1
  ([`01b25cd`](https://github.com/lugovskovp/QGIS_VDO/commit/01b25cd13a255521e80041bcc7da0494493c9667))

- **block)0x06**: Poi, собранные по географии
  ([`9d829f8`](https://github.com/lugovskovp/QGIS_VDO/commit/9d829f8dc51547288f4ebd5f0b081145457fa413))

### Performance Improvements

- Test_block_0x10 — оптимизация тестового покрытия POI
  ([`36b4013`](https://github.com/lugovskovp/QGIS_VDO/commit/36b4013350886fcdd05756ecd3e659c85daeaf44))

- Убрал избыточную memoryview и закомментированный код
  ([`bcaa7c2`](https://github.com/lugovskovp/QGIS_VDO/commit/bcaa7c209ad907729c78db3b6cdd1cc2ef2a39c8))

### Refactoring

- Get_poi - полная информация, быстро
  ([`9d5c8ce`](https://github.com/lugovskovp/QGIS_VDO/commit/9d5c8ce8ee0fddb990428f2a6e4765156c4fe57a))

- Gigacode review
  ([`59c3fa3`](https://github.com/lugovskovp/QGIS_VDO/commit/59c3fa301f2f5d7e7dc5e11f554bd83694fdce67))

- Slots, get_all_items
  ([`ec94e99`](https://github.com/lugovskovp/QGIS_VDO/commit/ec94e99b4c52a0488d98c4957eca57cdc375c144))

- Быстродействие, tested 100%
  ([`0c62d27`](https://github.com/lugovskovp/QGIS_VDO/commit/0c62d2782d4447a69c4c5e62b9f6eaecc2baaf5e))

- Переписал block_0x10 — get_poi всегда загружает детали, get_all_brifs с memoryview
  ([`8f66a5d`](https://github.com/lugovskovp/QGIS_VDO/commit/8f66a5d0ce9983cd3a7c5e8f5f2f75bc0a355f30))

- Экономия на итерацию: 2 аллокации (pack + memoryview) × 466K POI = ~1M лишних объектов не
  создаётся.
  ([`1de3212`](https://github.com/lugovskovp/QGIS_VDO/commit/1de32128a94bd6303931cf88647f4323dd694ec0))


## v1.0.0-dev.27 (2026-10-14)

### Chores

- Agents rules
  ([`d8d150a`](https://github.com/lugovskovp/QGIS_VDO/commit/d8d150a513c7bc766b702ce87a89026d4fe36df4))

### Documentation

- Обновить README и переместить секцию useful в NOTES.md
  ([`6bde897`](https://github.com/lugovskovp/QGIS_VDO/commit/6bde897232e4981fcdfba05dcd345c7eb3f72686))

### Refactoring

- Bitstream — закомментировать touch, ValueError → NotImplementedError
  ([`d1170d3`](https://github.com/lugovskovp/QGIS_VDO/commit/d1170d3c2d606202086c61e4da0110f4223069c3))


## v1.0.0-dev.26 (2026-10-14)

### Bug Fixes

- Coverage badge show only main pushes
  ([`7d4782e`](https://github.com/lugovskovp/QGIS_VDO/commit/7d4782e323da09180d9768e75c481071bd4abb8e))


## v1.0.0-dev.25 (2026-10-14)


## v1.0.0-dev.24 (2026-10-14)

### Bug Fixes

- $GITHUB_ENV
  ([`724dc19`](https://github.com/lugovskovp/QGIS_VDO/commit/724dc194d16d571548f9f5f5f8e2167d71376d2e))

- $GITHUB_OUTPUT
  ([`2af0dde`](https://github.com/lugovskovp/QGIS_VDO/commit/2af0dde28721b44d4f571c69b19ebd5e8f2b842c))

- $REAL_PATH version --no-push
  ([`e9a19b4`](https://github.com/lugovskovp/QGIS_VDO/commit/e9a19b471030fac29f69aff6a82677d90cf31bcc))

- --ignore-installed
  ([`d16cc2a`](https://github.com/lugovskovp/QGIS_VDO/commit/d16cc2abc2774741dedf0aff085d2553d2c3bdec))

- 2 strings
  ([`e3a60d7`](https://github.com/lugovskovp/QGIS_VDO/commit/e3a60d767d2ef408989c358a96d444180516299f))

- Add bitarray module into docker
  ([`6e1264b`](https://github.com/lugovskovp/QGIS_VDO/commit/6e1264bef065c440a9f5ddc94d01f0a737d68542))

- Angular -> conventional
  ([`096c18c`](https://github.com/lugovskovp/QGIS_VDO/commit/096c18c73883ac5e361e8d67669513e445c2336f))

- C:/temp in linux
  ([`2ba76d5`](https://github.com/lugovskovp/QGIS_VDO/commit/2ba76d5d48f26703a385f9c130d9b1451d7f1cf1))

- Changelog_file = "CHANGELOG.md"
  ([`0042b00`](https://github.com/lugovskovp/QGIS_VDO/commit/0042b00519d0b8b296f90e9f0b7e5247bafe7932))

- Commit_parser = "scipy"
  ([`af2d5f6`](https://github.com/lugovskovp/QGIS_VDO/commit/af2d5f615173921b226cf9c5b6e0375de481c986))

- Container qgis
  ([`6daf13d`](https://github.com/lugovskovp/QGIS_VDO/commit/6daf13d9ce31f38913d1b2f7b116c176db3a2b9b))

- Del pytest-qgis
  ([`819eace`](https://github.com/lugovskovp/QGIS_VDO/commit/819eacefe7d983df27425577ef010ae1ec4678fe))

- Env pythonpath
  ([`738ca2c`](https://github.com/lugovskovp/QGIS_VDO/commit/738ca2c223d1b78f36a9285b3e5de34cbca13fdf))

- Env pythonpath
  ([`c14bfdf`](https://github.com/lugovskovp/QGIS_VDO/commit/c14bfdfdf778762fb3f85ed601132f8ec6638a20))

- Export path, $PATH_EXIT
  ([`18b87f6`](https://github.com/lugovskovp/QGIS_VDO/commit/18b87f6372b724692c64f88d83d5e37bcd4b1388))

- Export PATH=
  ([`b780a9d`](https://github.com/lugovskovp/QGIS_VDO/commit/b780a9dc0306810d9a7a30c53412f035d30cfe99))

- Fix home directory
  ([`ea193e3`](https://github.com/lugovskovp/QGIS_VDO/commit/ea193e3c500911131491cddf3f57103c474e94aa))

- Gen badge
  ([`dbb622a`](https://github.com/lugovskovp/QGIS_VDO/commit/dbb622ada10c7b0d68b260cf7296430b0458030a))

- Gh-output
  ([`b642d1a`](https://github.com/lugovskovp/QGIS_VDO/commit/b642d1a4d2f20fb03e65b83ed105d4ef983d2b1b))

- Gist
  ([`3e18952`](https://github.com/lugovskovp/QGIS_VDO/commit/3e18952e0e0035440d0d40e4159a3e4c4b1885ac))

- Git доверять текущей рабочей директории
  ([`f95f677`](https://github.com/lugovskovp/QGIS_VDO/commit/f95f677026073778a4baba6420cb876ce6bb10ac))

- Hatch path
  ([`f6287ca`](https://github.com/lugovskovp/QGIS_VDO/commit/f6287cad7065bcd8a00e4b6ff342d0cc49c072d4))

- Hatch: not found
  ([`f3cb60c`](https://github.com/lugovskovp/QGIS_VDO/commit/f3cb60cea4713fe044ddf56717b52c21c11fb8f7))

- HATCH_BUILD_NO_ISOLATION=1 hatch build --target sdist
  ([`8003181`](https://github.com/lugovskovp/QGIS_VDO/commit/8003181a5a46a5e30e2806e3671239673864d8be))

- NEW_VERSION
  ([`dee3b3c`](https://github.com/lugovskovp/QGIS_VDO/commit/dee3b3ccfca97a10e421ca7f3d54d7bf24f76725))

- PYTEST_EXIT
  ([`5d53386`](https://github.com/lugovskovp/QGIS_VDO/commit/5d53386aad4206279bbcddf1fc77b448088dc815))

- Python-semantic-release
  ([`5bdbfc4`](https://github.com/lugovskovp/QGIS_VDO/commit/5bdbfc40fca8b6eae68d91b039a1ffb91bcaa769))

- Python-semantic-release
  ([`1742be9`](https://github.com/lugovskovp/QGIS_VDO/commit/1742be9735d0eae5990feb783d0a34d67fe1b19f))

- Python3 -m semantic_release version --no-push
  ([`c4785bb`](https://github.com/lugovskovp/QGIS_VDO/commit/c4785bb8d62f0514e3206c51d44f36a28ac6b2c1))

- Pythonpath
  ([`dc50cba`](https://github.com/lugovskovp/QGIS_VDO/commit/dc50cbaf87e0a71ff8406065b734e8cbdaeb5724))

- PYTHONPATH=/usr/local
  ([`df66548`](https://github.com/lugovskovp/QGIS_VDO/commit/df6654848025584bad9e996d078131c3144424af))

- Readme Coverage, Issues, Release Настроить ci workflow GitHub Actions
  ([`2da4c20`](https://github.com/lugovskovp/QGIS_VDO/commit/2da4c20868e15978df61978000477f50bd7ccf68))

- Rem REAL_PATH
  ([`7e12c02`](https://github.com/lugovskovp/QGIS_VDO/commit/7e12c0266cd0b9c599c7724708eaad7a5c62e889))

- Repair escaped chars
  ([`199e070`](https://github.com/lugovskovp/QGIS_VDO/commit/199e0707e754f0705a728728fdca65bb646443f7))

- Shell: bash
  ([`75a5cf0`](https://github.com/lugovskovp/QGIS_VDO/commit/75a5cf05ca7927ba729ecc0dfe2d36329840c2d9))

- Shell: bash
  ([`878d43d`](https://github.com/lugovskovp/QGIS_VDO/commit/878d43d38d396430d496a3fb7e03153842e87868))

- Test w/o mock
  ([`8b4a218`](https://github.com/lugovskovp/QGIS_VDO/commit/8b4a21859c374654cac67c4748e1a67b29c369f2))

- Toml
  ([`069e09c`](https://github.com/lugovskovp/QGIS_VDO/commit/069e09c120c3a6fa85955f2cb28ba2199a265502))

- Uncomment dependencies = ["bitarray"] for github tests
  ([`cfcd34e`](https://github.com/lugovskovp/QGIS_VDO/commit/cfcd34ee483f250457af3cab47007e1084414303))

- Upgrade pip packaging
  ([`2c911a8`](https://github.com/lugovskovp/QGIS_VDO/commit/2c911a848852a9b007ba7aeea3277808d248704c))

- URIs: https://qgis.org/ubuntu-ltr
  ([`1100f1f`](https://github.com/lugovskovp/QGIS_VDO/commit/1100f1ff755ea75f735039876282c635e1492739))

- Use docker again
  ([`2cd48aa`](https://github.com/lugovskovp/QGIS_VDO/commit/2cd48aa0aedc0613faf4b3349d422e29c5828508))

- Verbose
  ([`374859a`](https://github.com/lugovskovp/QGIS_VDO/commit/374859a2d8dd32421e8d3fa3365151f9cbb06e70))

- Временный PYTHONPATH
  ([`89388ce`](https://github.com/lugovskovp/QGIS_VDO/commit/89388cebcf44b2a8a764a1d67ccd9dd93a500232))

- Импорт через keyserver вместо wget
  ([`b7bdf92`](https://github.com/lugovskovp/QGIS_VDO/commit/b7bdf92879929034d78adb3e3fd2de8d4b2e38cc))

- Исправил синтаксис GitHub Actions — заэкранированные переменные и команды
  ([`087fbdc`](https://github.com/lugovskovp/QGIS_VDO/commit/087fbdccf9202ba54838f0784cf98196531c53b4))

- Правильные xttp пути в yml
  ([`cea89ed`](https://github.com/lugovskovp/QGIS_VDO/commit/cea89eddaa36b8897cfed875002ce3716a6640f9))

- Сначала новые пакеты из pip (/usr/local),
  ([`e69715d`](https://github.com/lugovskovp/QGIS_VDO/commit/e69715d150dfe0cea4c493cc2a8cdc255482f348))

- Убрали вызовы gpg --keyserver
  ([`9ddda60`](https://github.com/lugovskovp/QGIS_VDO/commit/9ddda60fab890e537158e1459876d9bc69922ee9))


## v1.0.0-dev.17 (2026-10-13)

- Initial Release
