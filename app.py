from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


# Классы из вашего исходного кода
class Reservoir:
    def __init__(self, name, initial_pressure, oil_volume, gas_volume):
        self.name = name
        self.initial_pressure = initial_pressure
        self.current_pressure = initial_pressure
        self.oil_volume = oil_volume
        self.gas_volume = gas_volume
        self.production_history = []

    def produce(self, amount_oil, amount_gas):
        if amount_oil > self.oil_volume or amount_gas > self.gas_volume:
            raise ValueError("Недостаточно ресурсов в месторождении")

        self.oil_volume -= amount_oil
        self.gas_volume -= amount_gas
        pressure_drop = (amount_oil / (self.oil_volume + amount_oil)) * self.current_pressure * 0.1
        self.current_pressure -= pressure_drop
        self.production_history.append({
            "oil": amount_oil,
            "gas": amount_gas,
            "pressure": self.current_pressure
        })

        return {"oil": amount_oil, "gas": amount_gas}

    def get_status(self):
        total_produced = sum(p["oil"] for p in self.production_history)
        initial_total = self.oil_volume + total_produced
        depletion = (total_produced / initial_total * 100) if initial_total > 0 else 0

        return {
            "name": self.name,
            "current_pressure": round(self.current_pressure, 2),
            "oil_volume": round(self.oil_volume, 2),
            "gas_volume": round(self.gas_volume, 2),
            "depletion": round(depletion, 2)
        }


class Well:
    def __init__(self, name, reservoir, max_production_rate):
        self.name = name
        self.reservoir = reservoir
        self.max_production_rate = max_production_rate
        self.is_active = True

    def calculate_production(self, days, current_day=0, total_oil=0, total_gas=0):
        if current_day >= days or not self.is_active:
            return {"oil": total_oil, "gas": total_gas}

        pressure_factor = self.reservoir.current_pressure / self.reservoir.initial_pressure
        possible_oil = min(
            self.max_production_rate * pressure_factor,
            self.reservoir.oil_volume
        )
        possible_gas = min(
            self.max_production_rate * 1000 * pressure_factor,
            self.reservoir.gas_volume
        )

        if possible_oil <= 0 or possible_gas <= 0:
            self.is_active = False
            return {"oil": total_oil, "gas": total_gas}

        produced = self.reservoir.produce(possible_oil, possible_gas)

        return self.calculate_production(
            days, current_day + 1,
                  total_oil + produced["oil"],
                  total_gas + produced["gas"]
        )

    def get_status(self):
        return {
            "name": self.name,
            "is_active": self.is_active,
            "max_production": self.max_production_rate,
            "reservoir": self.reservoir.name
        }


# Глобальные объекты
reservoir = None
well = None


@app.route('/')
def index():
    return render_template('index.html')


# API endpoints
@app.route('/api/create_reservoir', methods=['POST'])
def api_create_reservoir():
    global reservoir
    data = request.json
    try:
        reservoir = Reservoir(
            data['name'],
            float(data['pressure']),
            float(data['oil']),
            float(data['gas'])
        )
        return jsonify({"success": True, "message": "Месторождение создано"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/create_well', methods=['POST'])
def api_create_well():
    global well, reservoir
    if not reservoir:
        return jsonify({"success": False, "message": "Сначала создайте месторождение"}), 400

    data = request.json
    try:
        well = Well(
            data['name'],
            reservoir,
            float(data['rate'])
        )
        return jsonify({"success": True, "message": "Скважина создана"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/reservoir_status')
def api_reservoir_status():
    if not reservoir:
        return jsonify({"success": False, "message": "Месторождение не создано"}), 404
    return jsonify({"success": True, "data": reservoir.get_status()})


@app.route('/api/well_status')
def api_well_status():
    if not well:
        return jsonify({"success": False, "message": "Скважина не создана"}), 404
    return jsonify({"success": True, "data": well.get_status()})


@app.route('/api/calculate_production', methods=['POST'])
def api_calculate_production():
    if not well:
        return jsonify({"success": False, "message": "Скважина не создана"}), 404

    try:
        days = int(request.json['days'])
        result = well.calculate_production(days)
        return jsonify({
            "success": True,
            "data": {
                "oil": result["oil"],
                "gas": result["gas"],
                "history": reservoir.production_history
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/single_production', methods=['POST'])
def api_single_production():
    if not reservoir:
        return jsonify({"success": False, "message": "Месторождение не создано"}), 404

    try:
        oil = float(request.json['oil'])
        gas = float(request.json['gas'])
        result = reservoir.produce(oil, gas)
        return jsonify({
            "success": True,
            "data": {
                "oil": result["oil"],
                "gas": result["gas"],
                "history": reservoir.production_history
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/test')
def test_api():
    return jsonify({
        "status": "success",
        "message": "Сервер готов к работе! Создайте месторождение через /api/create_reservoir"
    })
if __name__ == '__main__':
    app.run(debug=True)