var ThermostatInstances=[];

function updateThermostat(data)
{
	for (index in ThermostatInstances)
	{
		if (ThermostatInstances[index].valueVARpk == data.pk)
		{
			ThermostatInstances[index].ambient_temperature=data.Value;
		}
		if (ThermostatInstances[index].targetVARpk == data.pk)
		{
			var check=ThermostatInstances[index].is_true;
			clearInterval(ThermostatInstances[index].acknowledged);
			ThermostatInstances[index].target_temperature=data.Value;
		}
	}
}


var thermostatDial = (function() {
	
	/*
	 * Utility functions
	 */
	
	// Create an element with proper SVG namespace, optionally setting its attributes and appending it to another element
	function createSVGElement(tag,attributes,appendTo) {
		var element = document.createElementNS('http://www.w3.org/2000/svg',tag);
		attr(element,attributes);
		if (appendTo) {
			appendTo.appendChild(element);
		}
		return element;
	}
	
	// Set attributes for an element
	function attr(element,attrs) {
		for (var i in attrs) {
			element.setAttribute(i,attrs[i]);
		}
	}
	
	// Rotate a cartesian point about given origin by X degrees
	function rotatePoint(point, angle, origin) {
		var radians = angle * Math.PI/180;
		var x = point[0]-origin[0];
		var y = point[1]-origin[1];
		var x1 = x*Math.cos(radians) - y*Math.sin(radians) + origin[0];
		var y1 = x*Math.sin(radians) + y*Math.cos(radians) + origin[1];
		return [x1,y1];
	}
	
	// Rotate an array of cartesian points about a given origin by X degrees
	function rotatePoints(points, angle, origin) {
		return points.map(function(point) {
			return rotatePoint(point, angle, origin);
		});
	}
	
	// Given an array of points, return an SVG path string representing the shape they define
	function pointsToPath(points) {
		return points.map(function(point, iPoint) {
			return (iPoint>0?'L':'M') + point[0] + ' ' + point[1];
		}).join(' ')+'Z';
	}
	
	function circleToPath(cx, cy, r) {
		return [
			"M",cx,",",cy,
			"m",0-r,",",0,
			"a",r,",",r,0,1,",",0,r*2,",",0,
			"a",r,",",r,0,1,",",0,0-r*2,",",0,
			"z"
		].join(' ').replace(/\s,\s/g,",");
	}
	
	function donutPath(cx,cy,rOuter,rInner) {
		return circleToPath(cx,cy,rOuter) + " " + circleToPath(cx,cy,rInner);
	}
	
	// Restrict a number to a min + max range
	function restrictToRange(val,min,max) {
		if (val < min) return min;
		if (val > max) return max;
		return val;
	}
	
	// Round a number to the nearest 0.5
	function roundHalf(num) {
		return Math.round(num*2)/2;
	}
	
	function setClass(el, className, state) {
		el.classList[state ? 'add' : 'remove'](className);
	}
	
	/*
	 * The "MEAT"
	 */

	return function(targetElement, options) {
		var self = this;
		
		/*
		 * Options
		 */
		options = options || {};
		options = {
			diameter: options.diameter || 400,
			minValue: options.minValue, // Minimum value for target temperature
			maxValue: options.maxValue, // Maximum value for target temperature
			numTicks: options.numTicks || 150, // Number of tick lines to display around the dial
			tickDegrees: options.tickDegrees ||300, //  Degrees of the dial that should be covered in tick lines
			onSetTargetTemperature: options.onSetTargetTemperature || function() {}, // Function called when new target temperature set by the dial
			initialTarget: options.initialTarget||0,
			initialValue: options.initialValue||0,
			targetVARpk: options.targetVARpk,
			valueVARpk: options.valueVARpk,
			hysteresis: options.hysteresis,
			operator: options.operator,
		};
		
		/*
		 * Properties - calculated from options in many cases
		 */
		var properties = {
			tickDegrees: options.tickDegrees, //  Degrees of the dial that should be covered in tick lines
			rangeValue: options.maxValue - options.minValue,
			radius: options.diameter/2,
			ticksOuterRadius: options.diameter / 30,
			ticksInnerRadius: options.diameter / 8,
			hvac_states: ['off', 'heating', 'cooling'],
			dragLockAxisDistance: 15,
		}
		properties.lblAmbientPosition = [properties.radius, properties.ticksOuterRadius-(properties.ticksOuterRadius-properties.ticksInnerRadius)/2]
		properties.offsetDegrees = 180-(360-properties.tickDegrees)/2;
		
		/*
		 * Object state
		 */
		var state = {
			valueVARpk: options.valueVARpk,
			targetVARpk: options.targetVARpk,
			target_temperature: options.initialTarget,
			ambient_temperature: options.initialValue,
			hvac_state: properties.hvac_states[0],
			has_leaf: true,
			away: false,
			acknowledged:null,
			is_true:false,
			tendency:0,
		};
		
		/*
		 * Property getter / setters
		 */
		
		Object.defineProperty(this,'hysteresis',{
			get: function() {
				return options.hysteresis;
			},
			set: function(val) {
				options.hysteresis = val;
			}
		});
		Object.defineProperty(this,'operator',{
			get: function() {
				return options.operator;
			},
			set: function(val) {
				options.operator = val;
			}
		});
		Object.defineProperty(this,'acknowledged',{
			get: function() {
				for (i in icoWifi)
				{
					setClass(icoWifi[i],'dial_ico_wifiNOOK',false);
				}
				return state.acknowledged;
			},
			set: function(val) {
				state.acknowledged = val;
			}
		});
		Object.defineProperty(this,'tendency',{
			get: function() {
				return state.tendency;
			},
			set: function(val) {
				state.tendency = val;
				render();
			}
		});
		Object.defineProperty(this,'valueVARpk',{
			get: function() {
				return state.valueVARpk;
			},
			set: function(val) {
				state.valueVARpk = val;
			}
		});
		Object.defineProperty(this,'targetVARpk',{
			get: function() {
				return state.targetVARpk;
			},
			set: function(val) {
				state.targetVARpk = val;
			}
		});
		Object.defineProperty(this,'target_temperature',{
			get: function() {
				return state.target_temperature;
			},
			set: function(val) {
				state.target_temperature = restrictTargetTemperature(+val);
				render();
			}
		});
		Object.defineProperty(this,'ambient_temperature',{
			get: function() {
				return state.ambient_temperature;
			},
			set: function(val) {
				state.ambient_temperature = val;
				render();
			}
		});
		Object.defineProperty(this,'hvac_state',{
			get: function() {
				return state.hvac_state;
			},
			set: function(val) {
				if (properties.hvac_states.indexOf(val)>=0) {
					state.hvac_state = val;
					render();
				}
			}
		});
		Object.defineProperty(this,'has_leaf',{
			get: function() {
				return state.has_leaf;
			},
			set: function(val) {
				state.has_leaf = !!val;
				render();
			}
		});
		Object.defineProperty(this,'away',{
			get: function() {
				return state.away;
			},
			set: function(val) {
				state.away = !!val;
				render();
			}
		});
		Object.defineProperty(this,'is_true',{
			get: function() {
				checkIsTrue();
				return state.is_true;
			},
			set: function(val) {
				state.is_true = val;
				render();
			}
		});
		/*
		 * SVG
		 */
		var svg = createSVGElement('svg',{
			width: '100%', //options.diameter+'px',
			height: '100%', //options.diameter+'px',
			viewBox: '0 0 '+options.diameter+' '+options.diameter,
			class: 'dial'
		},targetElement);
		// CIRCULAR DIAL
		var circle = createSVGElement('circle',{
			cx: properties.radius,
			cy: properties.radius,
			r: properties.radius,
			class: 'dial__shape'
		},svg);
		// EDITABLE INDICATOR
		var editCircle = createSVGElement('path',{
			d: donutPath(properties.radius,properties.radius,properties.radius-4,properties.radius-8),
			class: 'dial__editableIndicator',
		},svg);
		
		/*
		 * Ticks
		 */
		var ticks = createSVGElement('g',{
			class: 'dial__ticks'	
		},svg);
		var tickPoints = [
			[properties.radius-1, properties.ticksOuterRadius],
			[properties.radius+1, properties.ticksOuterRadius],
			[properties.radius+1, properties.ticksInnerRadius],
			[properties.radius-1, properties.ticksInnerRadius]
		];
		var tickPointsLarge = [
			[properties.radius-1.5, properties.ticksOuterRadius],
			[properties.radius+1.5, properties.ticksOuterRadius],
			[properties.radius+1.5, properties.ticksInnerRadius+20],
			[properties.radius-1.5, properties.ticksInnerRadius+20]
		];
		var theta = properties.tickDegrees/options.numTicks;
		var tickArray = [];
		for (var iTick=0; iTick<options.numTicks; iTick++) {
			tickArray.push(createSVGElement('path',{d:pointsToPath(tickPoints)},ticks));
		};
		
		/*
		 * Labels
		 */
		var lblTarget = createSVGElement('text',{
			x: properties.radius,
			y: properties.radius,
			class: 'dial__lbl dial__lbl--target'
		},svg);
		var lblTarget_text = document.createTextNode('');
		lblTarget.appendChild(lblTarget_text);
		//
		var lblTargetHalf = createSVGElement('text',{
			x: properties.radius + properties.radius/2.5,
			y: properties.radius - properties.radius/8,
			class: 'dial__lbl dial__lbl--target--half'
		},svg);
		var lblTargetHalf_text = document.createTextNode('5');
		lblTargetHalf.appendChild(lblTargetHalf_text);
		//
		var lblAmbient = createSVGElement('text',{
			class: 'dial__lbl dial__lbl--ambient'
		},svg);
		var lblAmbient_text = document.createTextNode('');
		lblAmbient.appendChild(lblAmbient_text);
		//
		var lblAmbientHalf = createSVGElement('text',{
			class: 'dial__lbl dial__lbl--ambient--half'
		},svg);
		var lblAmbientHalf_text = document.createTextNode('');
		lblAmbientHalf.appendChild(lblAmbientHalf_text);
		//
		var lblAway = createSVGElement('text',{
			x: properties.radius,
			y: properties.radius,
			class: 'dial__lbl dial__lbl--away'
		},svg);
		var lblAway_text = document.createTextNode('AWAY');
		lblAway.appendChild(lblAway_text);
		
		/*
		 * WIFI ICON
		 */
		var leafScale = properties.radius/5/10;
		var wifiDef3=["M",9.9,5,"C",6.8,5,4,6.4,2.2,8.7,"l",1.1,1.1,"c",1.6,-2,4,-3.2,6.7,-3.2,"c",2.7,0,5.1,1.3,6.7,3.2,"l",1.1,-1.1,"C",15.8,6.4,13,5,9.9,5,"z"].map(function(x) {
			return isNaN(x) ? x : x*leafScale;
		}).join(' ');
		var wifiDef2=["M",9.9,8,"c",-2.3,0,-4.3,1.1,-5.6,2.8,"l",1.1,1.1,"c",1,-1.4,2.6,-2.4,4.5,-2.4,"c",1.9,0,3.5,0.9,4.5,2.4,"l",1.1,-1.1,"C",14.2,9.1,12.2,8,9.9,8,"z"].map(function(x) {
			return isNaN(x) ? x : x*leafScale;
		}).join(' ');
		var wifiDef1=["M",9.9,11,"c",-1.5,0,-2.7,0.8,-3.4,2,"l",1.1,1.1,"c",0.4,-0.9,1.3,-1.6,2.3,-1.6,"s",2,0.7,2.3,1.6,"l",1.1,-1.1,"C",12.6,11.8,11.4,11,9.9,11,"z"].map(function(x) {
			return isNaN(x) ? x : x*leafScale;
		}).join(' ');
		var translate = [properties.radius-(leafScale*10*0.9),properties.radius*1.5]
		var icoWifi=[];
		icoWifi.push(createSVGElement('path',{
			class: 'dial_ico_wifiOK',
			d: wifiDef3,
			transform: 'translate('+translate[0]+','+translate[1]+')'
		},svg));
		icoWifi.push(createSVGElement('path',{
			class: 'dial_ico_wifiOK',
			d: wifiDef2,
			transform: 'translate('+translate[0]+','+translate[1]+')'
		},svg));
		icoWifi.push(createSVGElement('path',{
			class: 'dial_ico_wifiOK',
			d: wifiDef1,
			transform: 'translate('+translate[0]+','+translate[1]+')',
		},svg));
		icoWifi.push(createSVGElement('circle',{
			class: 'dial_ico_wifiOK',
			r: 1*leafScale,
			cx:9.9*leafScale,
			cy:15.3*leafScale,
			transform: 'translate('+translate[0]+','+translate[1]+')',
		},svg));
		var icoON=createSVGElement('circle',{
			class: 'dial_ico_isTrue',
			r: 3*leafScale,
			cx:9.9*leafScale,
			cy:-2*leafScale,
			transform: 'translate('+translate[0]+','+translate[1]+')',
		},svg);
		
		var icoTendencyX=18*leafScale;
		var icoTendencyY=-2*leafScale;
		var icoTendencySide=10*leafScale;
		var icoTendencyDOWN=createSVGElement('polygon',{
			class: 'ico_tendency',
			points: icoTendencyX.toString()+','+icoTendencyY.toString()+' '+(icoTendencyX+icoTendencySide).toString()+','+icoTendencyY.toString()+' '+(icoTendencyX+0.5*icoTendencySide).toString()+','+(icoTendencyY+0.5*icoTendencySide).toString()+' ',
			transform: 'translate('+translate[0]+','+translate[1]+')',
			//transform: 'translate('+translate[0]+','+translate[1]+') rotate(180,'+(icoTendencyX+0.5*icoTendencySide).toString()+','+icoTendencyY.toString()+')',
		},svg);
		var icoTendencyUP=createSVGElement('polygon',{
			class: 'ico_tendency',
			points: icoTendencyX.toString()+','+icoTendencyY.toString()+' '+(icoTendencyX+icoTendencySide).toString()+','+icoTendencyY.toString()+' '+(icoTendencyX+0.5*icoTendencySide).toString()+','+(icoTendencyY+0.5*icoTendencySide).toString()+' ',
			transform: 'translate('+translate[0]+','+translate[1]+') rotate(180,'+(icoTendencyX+0.5*icoTendencySide).toString()+','+icoTendencyY.toString()+')',
		},svg);		
		/*
		 * RENDER
		 */
		function render() {
			renderAway();
			renderHvacState();
			renderTicks();
			renderTargetTemperature();
			renderAmbientTemperature();
			renderLeaf();
			renderIsTrue();
			renderTendency();
		}
		render();
		
		function checkIsTrue()
		{
			if (self.operator.includes("&lt"))
			{
				if (self.ambient_temperature<self.target_temperature-self.hysteresis)
				{ state.is_true= true}
				if (self.ambient_temperature>self.target_temperature+self.hysteresis)
				{ state.is_true= false}
			}else
			{
				if (self.ambient_temperature>self.target_temperature+self.hysteresis)
				{ state.is_true= true}
				if (self.ambient_temperature<self.target_temperature-self.hysteresis)
				{ state.is_true= false}
			}
		}
		/*
		 * RENDER - ticks
		 */
		function renderTicks() {
			var vMin, vMax,txtStyle='';
			if (self.away) {
				vMin = self.ambient_temperature;
				vMax = vMin;
			} else {
				vMin = Math.min(self.ambient_temperature, self.target_temperature);
				vMax = Math.max(self.ambient_temperature, self.target_temperature);
				if (self.ambient_temperature>self.target_temperature) {
					txtStyle="fill: green";
				}else
				{
					txtStyle="fill: red";
				}
			}
			var min = restrictToRange(Math.round((vMin-options.minValue)/properties.rangeValue * options.numTicks),0,options.numTicks-1);
			var max = restrictToRange(Math.round((vMax-options.minValue)/properties.rangeValue * options.numTicks),0,options.numTicks-1);
			//
			tickArray.forEach(function(tick,iTick) {
				var isLarge = iTick==min || iTick==max;
				var isActive = iTick >= min && iTick <= max;
				attr(tick,{
					d: pointsToPath(rotatePoints(isLarge ? tickPointsLarge: tickPoints,iTick*theta-properties.offsetDegrees,[properties.radius, properties.radius])),
					class: isActive ? 'active' : '',
					style: isActive ? txtStyle:''
				});
			});
		}
	
		/*
		 * RENDER - ambient temperature
		 */
		function renderAmbientTemperature() {
			lblAmbient_text.nodeValue = Math.floor(self.ambient_temperature);
			var shiftX=0;
			if (self.ambient_temperature%1!=0) {
				var decimalPart = Math.floor(10*(self.ambient_temperature - Math.floor(self.ambient_temperature))).toFixed(0);
				lblAmbientHalf_text.nodeValue = decimalPart.toString();//'⁵'
				shiftX=4;
			}else
			{lblAmbientHalf_text.nodeValue='';
			}
			var peggedValue = restrictToRange(self.ambient_temperature, options.minValue, options.maxValue);
			degs = properties.tickDegrees * (peggedValue-options.minValue)/properties.rangeValue - properties.offsetDegrees;
			if (peggedValue > self.target_temperature) {
				degs += 8;
			} else {
				degs -= 8;
			}
			
			var pos = rotatePoint(properties.lblAmbientPosition,degs,[properties.radius, properties.radius]);
			attr(lblAmbient,{
				x: pos[0]-shiftX,
				y: pos[1]
			});
			attr(lblAmbientHalf,{
				x: pos[0]+16,
				y: pos[1]-4
			});
		}
		
		/*
		 * RENDER - tendency arrows
		 */
		function renderTendency() {
			setClass(icoTendencyUP,'up',self.tendency>=0);
			setClass(icoTendencyDOWN,'down',self.tendency<=0);
		}
		
		/*
		 * RENDER - target temperature
		 */
		function renderTargetTemperature() {
			lblTarget_text.nodeValue = Math.floor(self.target_temperature);
			setClass(lblTargetHalf,'shown',self.target_temperature%1!=0);
		}
		
		/*
		 * RENDER - leaf
		 */
		function renderLeaf() {
			setClass(svg,'has-leaf',self.has_leaf);
		}
		/*
		 * RENDER - is_true
		 */
		function renderIsTrue() {
			setClass(icoON,'is-true',self.is_true);
		}
		
		/*
		 * RENDER - HVAC state
		 */
		function renderHvacState() {
			Array.prototype.slice.call(svg.classList).forEach(function(c) {
				if (c.match(/^dial--state--/)) {
					svg.classList.remove(c);
				};
			});
			svg.classList.add('dial--state--'+self.hvac_state);
		}
		
		/*
		 * RENDER - away
		 */
		function renderAway() {
			svg.classList[self.away ? 'add' : 'remove']('away');
		}
		
		/*
		 * Drag to control
		 */
		var _drag = {
			inProgress: false,
			startPoint: null,
			startTemperature: 0,
			lockAxis: undefined
		};
		
		function eventPosition(ev) {
			if (ev.targetTouches && ev.targetTouches.length) {
				return  [ev.targetTouches[0].clientX, ev.targetTouches[0].clientY];
			} else {
				return [ev.x, ev.y];
			};
		}
		
		var startDelay;
		function dragStart(ev) {
			startDelay = setTimeout(function() {
				setClass(svg, 'dial--edit', true);
				_drag.inProgress = true;
				_drag.startPoint = eventPosition(ev);
				_drag.startTemperature = self.target_temperature || options.minValue;
				_drag.lockAxis = undefined;
			},1000);
		};
		
		
		function dragEnd (ev) {
			clearTimeout(startDelay);
			setClass(svg, 'dial--edit', false);
			if (!_drag.inProgress) return;
			_drag.inProgress = false;
			if (self.target_temperature != _drag.startTemperature) {
				if (typeof options.onSetTargetTemperature == 'function') {
					options.onSetTargetTemperature(self.target_temperature);
					for (i in icoWifi)
					{
						setClass(icoWifi[i],'dial_ico_wifiNOOK',true);
					}
					state.acknowledged = setInterval(options.onSetTargetTemperature,2000,self.target_temperature);
				};
			};
		};
		
		function dragMove(ev) {
			ev.preventDefault();
			if (!_drag.inProgress) return;
			var evPos =  eventPosition(ev);
			var dy = _drag.startPoint[1]-evPos[1];
			var dx = evPos[0] - _drag.startPoint[0];
			var dxy;
			if (_drag.lockAxis == 'x') {
				dxy  = dx;
			} else if (_drag.lockAxis == 'y') {
				dxy = dy;
			} else if (Math.abs(dy) > properties.dragLockAxisDistance) {
				_drag.lockAxis = 'y';
				dxy = dy;
			} else if (Math.abs(dx) > properties.dragLockAxisDistance) {
				_drag.lockAxis = 'x';
				dxy = dx;
			} else {
				dxy = (Math.abs(dy) > Math.abs(dx)) ? dy : dx;
			};
			var dValue = (dxy*getSizeRatio())/(options.diameter)*properties.rangeValue;
			self.target_temperature = roundHalf(_drag.startTemperature+dValue);
		}
		
		svg.addEventListener('mousedown',dragStart);
		svg.addEventListener('touchstart',dragStart);
		
		svg.addEventListener('mouseup',dragEnd);
		svg.addEventListener('mouseleave',dragEnd);
		svg.addEventListener('touchend',dragEnd);
		
		svg.addEventListener('mousemove',dragMove);
		svg.addEventListener('touchmove',dragMove);
		//
		
		/*
		 * Helper functions
		 */
		function restrictTargetTemperature(t) {
			return restrictToRange(roundHalf(t),options.minValue,options.maxValue);
		}
		
		function angle(point) {
			var dx = point[0] - properties.radius;
			var dy = point[1] - properties.radius;
			var theta = Math.atan(dx/dy) / (Math.PI/180);
			if (point[0]>=properties.radius && point[1] < properties.radius) {
				theta = 90-theta - 90;
			} else if (point[0]>=properties.radius && point[1] >= properties.radius) {
				theta = 90-theta + 90;
			} else if (point[0]<properties.radius && point[1] >= properties.radius) {
				theta = 90-theta + 90;
			} else if (point[0]<properties.radius && point[1] < properties.radius) {
				theta = 90-theta+270;
			}
			return theta;
		};
		
		function getSizeRatio() {
			return options.diameter / targetElement.clientWidth;
		}
		
	};
})();

/* ==== */

